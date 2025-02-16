#price in int format 
#output format
#Add send time and get time of an order
#Modified binance order placement to big waittime and logging in ms
import time
import hmac
import hashlib
import asyncio
import logging
import uvloop
import orjson
import aiohttp
import queue
from typing import Optional
from collections import deque
from urllib.parse import urlencode
from unicorn_binance_websocket_api import BinanceWebSocketApiManager
from pybit.unified_trading import WebSocket as BybitWebSocket
from termcolor import colored
from datetime import datetime
from time import gmtime, strftime
import logging 
import logging.handlers
# Replace these with your actual API keys.
from ByBitAPI import PUBLIC_KEY as BYBIT_PUBLIC_KEY, PRIVATE_KEY as BYBIT_PRIVATE_KEY
from binanceApi import api_key as BINANCE_API_KEY, api_secret as BINANCE_API_SECRET

################# Configuration #################
SYMBOL = "ADAUSDT"
PRICE_MULTIPLIER = 10000
DIFF_MULTIPLIER = 100
QTY = 10
FEE = 24
PROFIT = 30
DIFF_STEP = 5
MAXCOUNT = 280 # Number of positions

# For Bybit Client
BYBIT_URL = "https://api.bybit.com"
DEFAULT_TIMEOUT = 5  # seconds

################# Global State #################
prices = {"binance": 0.0, "bybit": 0.0}
open_trades_LS = {}
open_trades_SL = {}
binance_price_queue = deque(maxlen=1)
bybit_price_queue = deque(maxlen=1)

evaluate_lock = asyncio.Lock()

################# Optimized Logging #################
class NanoSecondFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = time.localtime(record.created)
        ms = int(record.msecs)
        return f"{ct.tm_hour:02}:{ct.tm_min:02}:{ct.tm_sec:02}.{ms:03d}"

logger = logging.getLogger('HFT')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(NanoSecondFormatter('%(asctime)s %(message)s'))
logger.addHandler(console_handler)

file_handler = logging.FileHandler(f'HFT_{time.strftime("%Y%m%d")}.log')
file_handler.setFormatter(NanoSecondFormatter('%(asctime)s %(message)s'))
logger.addHandler(file_handler)

# When shutting down the application, stop the listener:
# listener.stop()
################# Bybit Order Functions #################
def create_bybit_signature(secret, params):
    # Create signature string by joining sorted key=value pairs.
    param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(secret.encode(), param_str.encode(), hashlib.sha256).hexdigest()

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
# Bybit V5 Client (Optimized)
# --------------------------
class BybitClient(BaseExchangeClient):
    def __init__(self, public_key, private_key):
        super().__init__(BYBIT_URL)
        self.public_key = public_key
        self.private_key = private_key

    async def place_order(self, side, qty, symbol=SYMBOL, position_idx=2):
        """
        Ultra-low latency order execution with hedge mode support.
        :param side: "Buy" or "Sell" (case-insensitive; will be capitalized)
        :param qty: Order quantity
        :param symbol: Trading symbol
        :param position_idx: 0=One-way, 1=Buy side, 2=Sell side.
                             Here we use 2 to mirror the original code.
        """
        logger.info(f"Creating bybit order")
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
        try: 
            logger.info(f"Sending bybit order attmpt")
            async with self.session.post(
                f"{self.base_url}/v5/order/create",
                json=params,
                headers={"Referer": "HFT_BOT_1.0"}
            ) as response:
                data = await response.json()
                logger.info(f"Received bybit response for order")
                if data.get("retCode") != 0:
                    logger.error(f"Bybit Error: {data}")
                    raise Exception(f"Bybit API Error: {data.get('retCode')} - {data.get('retMsg')}")
                logger.info(f"Bybit Order Executed: {data}")
                return data
        except Exception as e:
            # Log exceptions such as network errors or JSON parsing issues.
            logger.error(f"ByBit order failed: {str(e)}")
            await asyncio.sleep(0.001)

################# Binance Client (Working Version) #################
class BinanceClient:
    def __init__(self, api_key, api_secret):
        self.base_url = "https://fapi.binance.com"
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = aiohttp.ClientSession()
        self.sequence = 1

    async def place_order(self, params: dict):
        """Proven working order placement"""
        try:
            # Preserve original parameter structure
            order_params = {
                "symbol": SYMBOL,
                "side": params["side"].upper(),
                "type": "MARKET",
                "quantity": str(params["quantity"]),
                "positionSide": params["positionSide"].upper(),
                "newOrderRespType": "ACK",
                "timestamp": int(time.time() * 1000)
            }

            # Generate signature with original format
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                urlencode(order_params).encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            order_params["signature"] = signature

            logger.info(f"Sending binance order: {order_params}")
            
            async with self.session.post(
                f"{self.base_url}/fapi/v1/order",
                data=order_params,
                headers={"X-MBX-APIKEY": self.api_key}
            ) as response:
                data = await response.json()
                logger.info(f"Binance response: {data}")
                return data
                
        except Exception as e:
            logger.error(f"Binance order failed: {str(e)}")
            await asyncio.sleep(0.001)
            return None
        
async def binance_price_producer(manager, event):
    """Binance mark price feed (markPriceUpdate)"""
    while True:
        try:
            stream_data = manager.pop_stream_data_from_stream_buffer()
            if stream_data:
                # Decode bytes to str if needed.
                if isinstance(stream_data, bytes):
                    stream_data = stream_data.decode("utf-8")
                # Use orjson to decode JSON.
                if isinstance(stream_data, str):
                    try:
                        stream_data = orjson.loads(stream_data)
                    except Exception as e:
                        logger.error(
                            f"Failed to decode JSON from Binance: {e}, data: {stream_data}",
                            exc_info=True
                        )
                        continue

                # If data is nested under "data", extract it.
                if "data" in stream_data:
                    stream_data = stream_data["data"]

                # Process markPriceUpdate events.
                if stream_data.get("e") == "aggTrade":
                    if "p" in stream_data:
                        # Convert the price (as float) into an integer using PRICE_MULTIPLIER.
                        price = int(float(stream_data.get("p", 0)) * PRICE_MULTIPLIER)
                        binance_price_queue.append(price)
                        prices["binance"] = price
                        event.set()
                    else:
                        logger.warning(f"Binance: 'p' not found in aggTrade event: {stream_data}")
                elif "result" in stream_data and stream_data["result"] is None:
                    logger.info(f"Binance: Subscription confirmation: {stream_data}")
                else:
                    logger.debug(f"Unhandled Binance data format: {stream_data}")
            await asyncio.sleep(0.001)
        except Exception as e:
            logger.error(f"Binance WS Error: {str(e)}")
            await asyncio.sleep(1)

async def bybit_price_producer(event):
    """Bybit price feed with connection management"""
    ws = None
    try:
        ws = BybitWebSocket(
            testnet=False,
            channel_type="linear",
            ping_interval=30,
            ping_timeout=10
        )
        def on_message(message):
            try:
                if message.get('topic') == f'tickers.{SYMBOL}':
                    price = int(float(message['data']['lastPrice']) * PRICE_MULTIPLIER)                    
                    bybit_price_queue.append(price)
                    prices["bybit"] = price
                    event.set()
            except Exception as e:
                logger.error(f"Bybit parse error: {str(e)}")

        ws.ticker_stream(symbol=SYMBOL, callback=on_message)
        while True:
            if not ws.is_connected():
                logger.warning("Bybit connection lost, reconnecting...")
                break
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Bybit WS Error: {str(e)}")
    finally:
        if ws:
            try:
                ws.exit()
            except Exception:
                pass
        await asyncio.sleep(1)
        await bybit_price_producer(event)

################# Price Processing #################
async def price_consumer():
    """Handle price updates with minimal latency"""
    while True:
        while binance_price_queue:
            prices["binance"] = binance_price_queue.popleft()
        while bybit_price_queue:
            prices["bybit"] = bybit_price_queue.popleft()
        await asyncio.sleep(0)

async def closeLS(position, diff, bybit_client: BybitClient, binance_client: BinanceClient):
    """Closes LS (Long Sell) positions in a structured parallel manner."""
    qtyToClose = open_trades_LS[position]['cnt']

    async with asyncio.TaskGroup() as tg:
        tg.create_task(binance_client.place_order({
            "side": "SELL",
            "positionSide": "LONG",
            "quantity": QTY
        }))
        tg.create_task(binance_client.place_order({
            "side": "BUY",
            "positionSide": "LONG",
            "quantity": QTY
        }))
        tg.create_task(bybit_client.place_order("Buy", qtyToClose, "ADAUSDT", 2))  # Close Bybit short
        tg.create_task(bybit_client.place_order("Sell", qtyToClose, "ADAUSDT", 2))  # Reopen Bybit short

    open_trades_LS[position]['cnt'] -= qtyToClose
    logger.info(f"Closed LS position {position} at diff {diff}")

    # Add new entry
    current_entry  = open_trades_LS.get(diff, {diff: diff, 'cnt': 0})
    current_entry['cnt'] += qtyToClose
    open_trades_LS[diff] = current_entry

async def closeSL(position, diff, bybit_client: BybitClient, binance_client: BinanceClient):
    """Closes SL (Short Long) positions using TaskGroup."""
    qtyToClose = open_trades_SL[position]['cnt']

    async with asyncio.TaskGroup() as tg:
        tg.create_task(binance_client.place_order({
            "side": "BUY",
            "positionSide": "SHORT",
            "quantity": qtyToClose
        }))
        tg.create_task(binance_client.place_order({
            "side": "SELL",
            "positionSide": "SHORT",
            "quantity": qtyToClose
        }))
        
        tg.create_task(bybit_client.place_order("Sell", qtyToClose, "ADAUSDT", 1))  # Close Bybit long
        tg.create_task(bybit_client.place_order("Buy", qtyToClose, "ADAUSDT", 1))  # Reopen Bybit long


    # Close profit entry
    open_trades_SL[position]['cnt'] -= qtyToClose
    logger.info(f"Closed SL position {position} at diff {diff}")

    # Add new entry
    current_entry  = open_trades_SL.get(diff, {diff: diff, 'cnt': 0})
    current_entry['cnt'] += qtyToClose
    open_trades_SL[diff] = current_entry

async def openPos(diff,bybit_client: BybitClient, binance_client: BinanceClient):
    """Opens positions in parallel using TaskGroup for efficiency."""
    async with asyncio.TaskGroup() as tg:
        tg.create_task(binance_client.place_order({
            "side": "BUY",
            "positionSide": "LONG",
            "quantity": QTY
        }))
        tg.create_task(binance_client.place_order({
            "side": "SELL",
            "positionSide": "SHORT",
            "quantity": QTY
        }))
        tg.create_task(bybit_client.place_order("Sell", QTY, "ADAUSDT", 2))  # Open Bybit short
        tg.create_task(bybit_client.place_order("Buy", QTY, "ADAUSDT", 1))  # Open Bybit long

    logger.info(f"Opened 4 positions on both Binance & Bybit for diff {diff} with binance price {prices['binance']} and bybit price {prices['bybit']}")

    
    # Add positions to LS and SL
    current_entry  = open_trades_LS.get(diff, {diff: diff, 'cnt': 0})
    current_entry['cnt'] += QTY
    open_trades_LS[diff] = current_entry

    current_entry  = open_trades_SL.get(diff, {diff: diff, 'cnt': 0})
    current_entry['cnt'] += QTY
    open_trades_SL[diff] = current_entry

################# Trading Strategy ################# 
async def trading_strategy(price_update_event, close_event,
                            bybit_client: BybitClient, binance_client: BinanceClient):
    """Core arbitrage strategy"""
    while True:
        await price_update_event.wait()
        price_update_event.clear()
        async with evaluate_lock:
            if prices["binance"] == 0 or prices["bybit"] == 0:
                continue
            try:

                binance_price = prices["binance"]
                bybit_price = prices["bybit"]
                spread = ((binance_price - bybit_price) * 100 * PRICE_MULTIPLIER) // binance_price
                diff = spread // (PRICE_MULTIPLIER // DIFF_MULTIPLIER)

                async with asyncio.TaskGroup() as tg:
                    ###################
                    ###################
                    ###################
                    ###PRIVATE LOGIC###
                    ###################
                    ###################
                    ###################
                    
            except Exception as e:
                logger.error(f"Strategy error: {str(e)}")
                await asyncio.sleep(1)

################# Price Display #################
async def display_prices():
    """Real-time price display"""
    while True:
        try:
            spread = ((prices["binance"] - prices["bybit"]) * 100 * PRICE_MULTIPLIER) // prices["binance"]
            spread = spread // (PRICE_MULTIPLIER // DIFF_MULTIPLIER)
            binance_price = prices["binance"] / PRICE_MULTIPLIER            
            bybit_price = prices["bybit"] / PRICE_MULTIPLIER
            binance_status = colored("ONLINE", "green") if binance_price > 0 else colored("OFFLINE", "red")
            bybit_status = colored("ONLINE", "green") if bybit_price > 0 else colored("OFFLINE", "red")
            output = (
                f"Binance [{binance_status}]: {colored(f'{binance_price:.5f}', 'white')} | "
                f"Bybit [{bybit_status}]: {colored(f'{bybit_price:.5f}', 'white')} | "
                f"Spread: {colored(f'{spread:.5f}', 'yellow')}"
            )
            print(f"\r{output}", end="", flush=True)
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Display error: {str(e)}")
            await asyncio.sleep(1)

async def calcPosToClose(ls: dict,sl: dict, close_event, bybit_client: BybitClient, binance_client: BinanceClient):
    while True:
        await close_event.wait()  # Wait until triggered
        close_event.clear()  # Reset event after execution

        if not ls or not sl:
            await asyncio.sleep(0)
            continue

        try:

            p1, p2 = prices["binance"], prices["bybit"]
            diff = ((p1 - p2) * 100 * PRICE_MULTIPLIER) // p1
            diff = diff // (PRICE_MULTIPLIER // DIFF_MULTIPLIER)

            #dct[diff] = {diff:2, 'cnt':6}
            count = 0
            qtyToClose = 0

            maxLS = max(ls.keys(), default=0) # Get max level of LS
            minSL = min(sl.keys(), default=0) # Get min level of SL


            # Optimized count calculation in one line
            count = sum(value['cnt'] for value in ls.values()) + sum(value['cnt'] for value in sl.values())

            if count > MAXCOUNT:
                if ls[maxLS]['cnt'] >= sl[minSL]['cnt']: # Close minSL - 1 postions
                    qtyToClose = max(0, sl[minSL]['cnt'] - QTY)
                else:
                    qtyToClose = max(0, ls[maxLS]['cnt'] - QTY)

                logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} calculated {qtyToClose} qty to close, maxLevelLS {maxLS}, actual minLevelSL {minSL}\nLS{ls}\nSL{sl}")
                
                # Using TaskGroup for efficient parallel execution
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(binance_client.place_order({
                        "side": "SELL",
                        "positionSide": "LONG",
                        "quantity": qtyToClose
                    })) # Close Binance long position
                    tg.create_task(binance_client.place_order({
                        "side": "BUY",
                        "positionSide": "SHORT",
                        "quantity": qtyToClose
                    })) # Close Binance short position
                    
                    tg.create_task(bybit_client.place_order("Buy", qtyToClose, "ADAUSDT", 2))  # Close Bybit short
                    tg.create_task(bybit_client.place_order("Sell", qtyToClose, "ADAUSDT", 1))  # Close Bybit long position

                # delete from diff closed positions
                ls[maxLS]['cnt'] -= qtyToClose
                sl[minSL]['cnt'] -= qtyToClose
                logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Successfully closed positions from calcPosToClose()\nLS{ls}\nSL{sl}")

        except Exception as e:
            logger.error(f"calcPosToClose Error: {e}")
            await asyncio.sleep(1)

################# Main Execution #################
async def main():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    price_update_event = asyncio.Event()
    close_event = asyncio.Event()  

    binance_ws = None
    # Initialize clients.
    bybit_client = BybitClient(BYBIT_PUBLIC_KEY, BYBIT_PRIVATE_KEY)
    binance_client = BinanceClient(BINANCE_API_KEY, BINANCE_API_SECRET)
    tasks = []
    try:
        binance_ws = BinanceWebSocketApiManager(
            exchange="binance.com-futures",
            output_default="dict"
        )
        # Subscribe to Binance trade channel to capture lastPrice.
        binance_ws.create_stream(
            channels=['aggTrade'],
            markets=[SYMBOL.lower()],
            stream_label="main_feed"

        )

        tasks = [
            asyncio.create_task(binance_price_producer(binance_ws, price_update_event)),
            asyncio.create_task(bybit_price_producer(price_update_event)),
            asyncio.create_task(price_consumer()),
            asyncio.create_task(trading_strategy(price_update_event, close_event, bybit_client, binance_client)),
            asyncio.create_task(display_prices()),
            asyncio.create_task(calcPosToClose(open_trades_LS, open_trades_SL, close_event, bybit_client, binance_client))
        ]
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutdown initiated")
    except Exception as e:
        logger.error(f"Main loop error: {str(e)}")
    finally:
        await binance_client.close()
        await bybit_client.close()
        if 'binance_ws' in locals():
            binance_ws.stop_manager_with_all_streams()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        print("\n")
        logger.info("System shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
