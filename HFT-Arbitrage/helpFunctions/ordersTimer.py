import time
import hmac
import hashlib
import asyncio
import logging
from urllib.parse import urlencode
import aiohttp
from datetime import datetime
from binanceApi import api_key, api_secret  # Replace with your actual imports
from ByBitAPI import PRIVATE_KEY, PUBLIC_KEY  # Replace with your actual imports

# Configure low-latency logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(handler)

# --------------------------
# HFT Configuration
# --------------------------
MAX_ORDER_QTY = 100
DEFAULT_TIMEOUT = 2
BINANCE_FUTURES_URL = "https://fapi.binance.com"
BYBIT_URL = "https://api.bybit.com"

# --------------------------
# Signature Generation
# --------------------------
def create_bybit_signature(secret, params):
    param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items()) if k != "sign"])
    return hmac.new(secret.encode(), param_str.encode(), hashlib.sha256).hexdigest()

def create_binance_signature(secret, params):
        # Binance requires EXACT parameter types (numbers as strings)
    params_str = "&".join(
        [f"{k}={v}" for k, v in sorted(params.items()) if not k == "signature"]
    )
    return hmac.new(
        secret.encode("utf-8"), 
        params_str.encode("utf-8"), 
        hashlib.sha256
    ).hexdigest()
# --------------------------

# --------------------------
# Base Client with Timing
# --------------------------
class BaseExchangeClient:
    def __init__(self, base_url, timeout=DEFAULT_TIMEOUT):
        self.base_url = base_url
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout),
            connector=aiohttp.TCPConnector(limit=100)
        )

    async def close(self):
        await self.session.close()

# --------------------------
# Binance Client Implementation
# --------------------------
class BinanceClient(BaseExchangeClient):
    def __init__(self, api_key, api_secret):
        super().__init__(BINANCE_FUTURES_URL)
        self.api_key = api_key
        self.api_secret = api_secret

    async def place_order(self, side, quantity, symbol="ADAUSDT", position_side="BOTH"):
        timing_data = {
            'start': time.perf_counter_ns(),
            'params_created': 0,
            'signature_generated': 0,
            'request_sent': 0,
            'response_received': 0
        }
        
        try:
            params = {
                "symbol": symbol,
                "side": side.upper(),
                "type": "MARKET",
                "quantity": f"{quantity:.4f}",
                "timestamp": int(time.time() * 1000),
                "positionSide": position_side.upper(),
                "recvWindow": "5000"
            }
            timing_data['params_created'] = time.perf_counter_ns()
            
            params["signature"] = create_binance_signature(self.api_secret, params)
            timing_data['signature_generated'] = time.perf_counter_ns()
            
            async with self.session.post(
                f"{self.base_url}/fapi/v1/order",
                headers={"X-MBX-APIKEY": self.api_key},
                data=params
            ) as response:
                timing_data['request_sent'] = time.perf_counter_ns()
                data = await response.json()
                timing_data['response_received'] = time.perf_counter_ns()
                
                metrics = self._calculate_metrics(timing_data, symbol, response.status == 200)
                self._log_metrics(metrics, "Binance")
                
                if response.status != 200:
                    raise Exception(f"API Error: {data.get('msg')}")
                return data, metrics
                
        except Exception as e:
            self._log_error(timing_data, e)
            raise

    def _calculate_metrics(self, timing_data, symbol, success):
        return {
            'exchange': 'binance',
            'symbol': symbol,
            'success': success,
            'total_ns': timing_data['response_received'] - timing_data['start'],
            'processing_ns': timing_data['signature_generated'] - timing_data['params_created'],
            'network_ns': timing_data['response_received'] - timing_data['request_sent'],
            'pre_send_ns': timing_data['request_sent'] - timing_data['start']
        }

    def _log_metrics(self, metrics, exchange):
        logger.info(
            f"{exchange} Order Timing || "
            f"Total: {metrics['total_ns']/1e6:.3f}ms | "
            f"Processing: {metrics['processing_ns']/1e6:.3f}ms | "
            f"Network: {metrics['network_ns']/1e6:.3f}ms | "
            f"Symbol: {metrics['symbol']} | "
            f"Status: {'Success' if metrics['success'] else 'Failed'}"
        )

    def _log_error(self, timing_data, error):
        elapsed = (time.perf_counter_ns() - timing_data['start'])/1e6
        logger.error(f"Order Failed after {elapsed:.3f}ms: {str(error)}")

# --------------------------
# Bybit Client Implementation
# --------------------------
class BybitClient(BaseExchangeClient):
    def __init__(self, public_key, private_key):
        super().__init__(BYBIT_URL)
        self.public_key = public_key
        self.private_key = private_key

    async def place_order(self, side, qty, symbol="ADAUSDT", position_idx=0):
        timing_data = {
            'start': time.perf_counter_ns(),
            'params_created': 0,
            'signature_generated': 0,
            'request_sent': 0,
            'response_received': 0
        }
        
        try:
            params = {
                "category": "linear",
                "symbol": symbol,
                "side": side.capitalize(),
                "orderType": "Market",
                "qty": str(qty),
                "positionIdx": position_idx,
                "api_key": self.public_key,
                "timestamp": str(int(time.time() * 1000)),
                "recv_window": "5000"
            }
            timing_data['params_created'] = time.perf_counter_ns()
            
            params["sign"] = create_bybit_signature(self.private_key, params)
            timing_data['signature_generated'] = time.perf_counter_ns()
            
            async with self.session.post(
                f"{self.base_url}/v5/order/create",
                json=params,
                headers={"Referer": "HFT_BOT_1.0"}
            ) as response:
                timing_data['request_sent'] = time.perf_counter_ns()
                data = await response.json()
                timing_data['response_received'] = time.perf_counter_ns()
                
                success = data.get("retCode") == 0
                metrics = self._calculate_metrics(timing_data, symbol, success)
                self._log_metrics(metrics, "Bybit")
                
                if not success:
                    raise Exception(f"API Error: {data.get('retMsg')}")
                return data, metrics
                
        except Exception as e:
            self._log_error(timing_data, e)
            raise

    def _calculate_metrics(self, timing_data, symbol, success):
        return {
            'exchange': 'bybit',
            'symbol': symbol,
            'success': success,
            'total_ns': timing_data['response_received'] - timing_data['start'],
            'processing_ns': timing_data['signature_generated'] - timing_data['params_created'],
            'network_ns': timing_data['response_received'] - timing_data['request_sent'],
            'pre_send_ns': timing_data['request_sent'] - timing_data['start']
        }

    def _log_metrics(self, metrics, exchange):
        logger.info(
            f"{exchange} Order Timing || "
            f"Total: {metrics['total_ns']/1e6:.3f}ms | "
            f"Processing: {metrics['processing_ns']/1e6:.3f}ms | "
            f"Network: {metrics['network_ns']/1e6:.3f}ms | "
            f"Symbol: {metrics['symbol']} | "
            f"Status: {'Success' if metrics['success'] else 'Failed'}"
        )

    def _log_error(self, timing_data, error):
        elapsed = (time.perf_counter_ns() - timing_data['start'])/1e6
        logger.error(f"Order Failed after {elapsed:.3f}ms: {str(error)}")

# --------------------------
# HFT Execution Engine
# --------------------------
class HFTEngine:
    def __init__(self):
        self.binance = BinanceClient(api_key, api_secret)
        self.bybit = BybitClient(PUBLIC_KEY, PRIVATE_KEY)

    async def execute(self, orders):
        execution_start = time.perf_counter_ns()
        tasks = []
        
        for order in orders:
            if order["exchange"] == "binance":
                tasks.append(self.binance.place_order(
                    side=order["side"],
                    quantity=order["quantity"],
                    symbol=order["symbol"],
                    position_side=order.get("position_side", "LONG")
                ))
            elif order["exchange"] == "bybit":
                tasks.append(self.bybit.place_order(
                    side=order["side"],
                    qty=order["quantity"],
                    symbol=order["symbol"],
                    position_idx=order.get("position_idx", 0)
                ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.perf_counter_ns() - execution_start
        
        successful = [r for r in results if not isinstance(r, Exception)]
        logger.info(
            f"\nAtomic Execution Summary || "
            f"Total Duration: {total_duration/1e6:.3f}ms | "
            f"Orders Attempted: {len(orders)} | "
            f"Orders Successful: {len(successful)} | "
            f"Success Rate: {len(successful)/len(orders):.1%}"
        )
        
        return self._process_results(results)

    def _process_results(self, results):
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Order Failed: {str(result)}")
            else:
                final_results.append(result[0])  # Return just the response data
        return final_results

    async def shutdown(self):
        await self.binance.close()
        await self.bybit.close()

# --------------------------
# Main Execution
# --------------------------
async def main():
    engine = HFTEngine()
    
    orders = [
        {
            "exchange": "binance",
            "symbol": "ADAUSDT",
            "side": "buy",
            "quantity": 10,
            "position_side": "LONG"
        },
        {
            "exchange": "bybit",
            "symbol": "ADAUSDT",
            "side": "sell",
            "quantity": 10,
            "position_idx": 2
        }
    ]
    
    try:
        results = await engine.execute(orders)
        logger.info("\nExecution Results Summary:")
        for result in results:
            logger.info(f"- {result.get('symbol')} Order ID: {result.get('orderId', result.get('result', {}).get('orderId'))}")
    except Exception as e:
        logger.error(f"Critical Error: {str(e)}")
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(main())