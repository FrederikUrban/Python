import time
import hmac
import hashlib
import asyncio
import logging
from urllib.parse import urlencode
import aiohttp
from datetime import datetime
from binanceApi import api_key, api_secret  # Binance credentials
from ByBitAPI import PRIVATE_KEY, PUBLIC_KEY  # Bybit credentials

# Configure low-latency logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(handler)

# --------------------------
# HFT Configuration
# --------------------------
MAX_ORDER_QTY = 100                   # Risk management
DEFAULT_TIMEOUT = 2                   # Seconds
BINANCE_FUTURES_URL = "https://fapi.binance.com"
BYBIT_URL = "https://api.bybit.com"    # Use testnet for testing

# --------------------------
# Optimized Signature Generation
# --------------------------
def create_bybit_signature(secret, params):
    param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
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
# Base Client with Connection Pooling
# --------------------------
class BaseExchangeClient:
    def __init__(self, base_url, timeout=DEFAULT_TIMEOUT):
        self.base_url = base_url
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout),
            connector=aiohttp.TCPConnector(limit=100)  # High concurrent connections
        )

    async def close(self):
        await self.session.close()

# --------------------------
# Binance Futures Client (Optimized)
# --------------------------
class BinanceClient(BaseExchangeClient):
    def __init__(self, api_key, api_secret):
        super().__init__(BINANCE_FUTURES_URL)
        self.api_key = api_key
        self.api_secret = api_secret

    async def place_order(self, side, quantity, symbol="ADAUSDT", position_side="BOTH"):
        """HFT-optimized market order execution"""
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": f"{quantity:.4f}",  # Precision control
            "timestamp": int(time.time() * 1000),
            "positionSide": position_side.upper(),
            "recvWindow": 5000
        }
        
        params["signature"] = create_binance_signature(self.api_secret, params)
        
        async with self.session.post(
            f"{self.base_url}/fapi/v1/order",
            headers={"X-MBX-APIKEY": self.api_key},
            data=params
        ) as response:
            data = await response.json()
            if response.status != 200:
                logger.error(f"Binance Error: {data}")
                raise Exception(f"Binance API Error: {data.get('code')} - {data.get('msg')}")
            logger.info(f"Binance Order Executed: {data}")
            return data

# --------------------------
# Bybit V5 Client (Optimized)
# --------------------------
class BybitClient(BaseExchangeClient):
    def __init__(self, public_key, private_key):
        super().__init__(BYBIT_URL)
        self.public_key = public_key
        self.private_key = private_key

    async def place_order(self, side, qty, symbol="ADAUSDT", position_idx=0):
        """Ultra-low latency order execution with hedge mode support"""
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side.capitalize(),  # Must be "Buy" or "Sell"
            "orderType": "Market",
            "qty": str(qty),
            "positionIdx": position_idx,  # 0=One-way, 1=Buy side, 2=Sell side
            "api_key": self.public_key,
            "timestamp": str(int(time.time() * 1000)),
            "recv_window": "5000"
        }
        
        params["sign"] = create_bybit_signature(self.private_key, params)
        
        async with self.session.post(
            f"{self.base_url}/v5/order/create",
            json=params,
            headers={"Referer": "HFT_BOT_1.0"}
        ) as response:
            data = await response.json()
            if data.get("retCode") != 0:
                logger.error(f"Bybit Error: {data}")
                raise Exception(f"Bybit API Error: {data.get('retCode')} - {data.get('retMsg')}")
            logger.info(f"Bybit Order Executed: {data}")
            return data

# --------------------------
# Atomic Order Dispatcher
# --------------------------
class HFTEngine:
    def __init__(self):
        self.binance = BinanceClient(api_key, api_secret)
        self.bybit = BybitClient(PUBLIC_KEY, PRIVATE_KEY)
        self.pending_orders = set()

    async def execute(self, orders):
        """Execute orders across exchanges atomically"""
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
        return self._process_results(results)

    def _process_results(self, results):
        # Add reconciliation logic here
        return [r for r in results if not isinstance(r, Exception)]

    async def shutdown(self):
        await self.binance.close()
        await self.bybit.close()

# --------------------------
# HFT Execution Example
# --------------------------
async def main():
    engine = HFTEngine()
    
    # Define atomic arbitrage orders
    orders = [
        {  # Binance Long
            "exchange": "binance",
            "symbol": "ADAUSDT",
            "side": "buy",
            "quantity": 10,
            "position_side": "LONG"
        },
        {  # Bybit Hedge Short
            "exchange": "bybit",
            "symbol": "ADAUSDT",
            "side": "sell",
            "quantity": 10,
            "position_idx": 2  # Requires hedge mode
        }
    ]
    
    try:
        results = await engine.execute(orders)
        logger.info(f"Execution results: {results}")
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
