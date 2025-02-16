from typing import Optional
import orjson  # Faster JSON library
from time import gmtime, strftime
import aiohttp
from ByBitAPI import PRIVATE_KEY, PUBLIC_KEY
from datetime import datetime
from urllib.parse import urlencode
from binanceApi import api_key, api_secret
import logging
import logging.handlers
import json
import asyncio
from unicorn_binance_websocket_api import BinanceWebSocketApiManager
import queue

################# Constants #################
PRICE_MULTIPLIER = 10000
DIFF_MULTIPLIER = 100
DIFF_STEP = 5
FEE = 24
PROFIT = 30
QTY = 10
BYBIT_WS = "wss://stream.bybit.com/v5/public/linear"
BINANCE_SYMBOL = "adausdt"
MAXCOUNT = 280 # Number of positions

################# Global Variables #################
prices = {"bybit": 0, "binance": 0}
open_trades_LS = {}
open_trades_SL = {}
evaluation_queue = asyncio.Queue(maxsize=1)
evaluate_lock = asyncio.Lock()

################# Logging Setup #################
log_queue = queue.Queue(-1)  # -1 indicates an infinite size

# Set up the QueueHandler with the queue.
queue_handler = logging.handlers.QueueHandler(log_queue)
logger = logging.getLogger('HFT')
logger.setLevel(logging.INFO)
logger.addHandler(queue_handler)

info_handler = logging.FileHandler(f'/root/hft/Log_{strftime("%d_%m_%Y", gmtime())}.csv', mode='a')
info_handler.addFilter(lambda r: r.levelno == logging.INFO)
error_handler = logging.FileHandler(f'/root/hft/ErrorLog_{strftime("%d_%m_%Y", gmtime())}.csv', mode='a')
error_handler.setLevel(logging.ERROR)

listener = logging.handlers.QueueListener(
    log_queue, info_handler, error_handler, respect_handler_level=True
)
listener.start()


# Precompute static elements
BINANCE_HEADERS = {"X-MBX-APIKEY": api_key}
BYBIT_ENDPOINT = "/v5/order/create"
BINANCE_ENDPOINT = "https://fapi.binance.com/fapi/v1/order"

# Initialize shared sessions during startup
binance_session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(limit=100),
    json_serialize=orjson.dumps
)

bybit_session = aiohttp.ClientSession(
    base_url="https://api.bybit.com",
    connector=aiohttp.TCPConnector(limit=100),
    json_serialize=orjson.dumps
)

################# Binance WebSocket Setup #################
binance_ws = BinanceWebSocketApiManager(exchange="binance.com-futures")
binance_ws.create_stream(["ticker"], [BINANCE_SYMBOL], output="UnicornFy")

################# Helper Functions #################
async def calcPosToClose(ls: dict,sl: dict):
    while True:
        async with evaluate_lock:
            try:

                if prices["binance"] == 0 or prices["bybit"] == 0:
                    continue
                p1, p2 = prices["binance"], prices["bybit"]
                diff = ((p1 - p2) * 100 * PRICE_MULTIPLIER) // p1
                diff = diff // (PRICE_MULTIPLIER // DIFF_MULTIPLIER)

                #dct[diff] = {diff:2, 'cnt':6}
                count = 0
                maxLS = 0
                minSL = 0
                qtyToClose = 0

                for i in ls:
                    count += i[diff]['cnt']
                    maxLS = max(i[diff][diff],maxLS) # Get max level of LS
                    # Yield control to the event loop
                    await asyncio.sleep(0)

                for i in sl:
                    count += i[diff]['cnt']
                    minSL = min(i[diff][diff],minSL) # Get min level of SL
                    # Yield control to the event loop
                    await asyncio.sleep(0)

                if count > MAXCOUNT:
                    if ls[maxLS]['cnt'] >= sl[minSL]['cnt']: # Close minSL - 1 postions
                        qtyToClose = sl[minSL]['cnt'] - QTY
                    else:
                        qtyToClose = ls[maxLS]['cnt'] - QTY

                    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} calculated {qtyToClose} qty to close, maxLevelLS {maxLS}, actual minLevelSL {minSL}\nLS{ls}\nSL{sl}")
                    
                    asyncio.create_task(place_order("binance",{"symbol": "ADAUSDT", "side": "SELL","position" : "LONG", "quantity": qtyToClose}))  # Close Binance long position
                    asyncio.create_task(place_order("binance",{"symbol": "ADAUSDT", "side": "BUY","position" : "SHORT", "quantity": qtyToClose}))  # Open Binance long position
                    asyncio.create_task(place_order("bybit", {"symbol": "ADAUSDT", "side": "Buy","position": 2, "qty": qtyToClose}))  # Open bybit short
                    asyncio.create_task(place_order("bybit", {"symbol": "ADAUSDT", "side": "Sell","position": 1, "qty": qtyToClose}))  # Open bybit short
                    
                    # delete from diff closed positions
                    ls[maxLS]['cnt'] =- qtyToClose
                    sl[minSL]['cnt'] =- qtyToClose
                    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Successfully closed positions from calcPosToClose()\nLS{ls}\nSL{sl}")

            except Exception as e:
                logger.error(f"calcPosToClose Error: {e}")

################# Trading Functions #################
async def place_order(
    exchange: str,
    params: dict,
    binance_session: aiohttp.ClientSession,
    bybit_session: aiohttp.ClientSession,
    max_retries: int = 3
) -> Optional[dict]:
    """Place order with optimized retry logic and shared sessions."""
    retries = 0
    last_error = None
    
    while retries < max_retries:
        try:
            if exchange == "bybit":
                async with bybit_session.post(
                    BYBIT_ENDPOINT,
                    json=params,  # Using JSON for Bybit V5 API
                    timeout=0.5  # Aggressive timeout for HFT
                ) as response:
                    data = await response.json(loads=orjson.loads)
                    if data.get("retCode") == 0:
                        return data
                    last_error = data.get("retMsg", "Unknown Bybit error")
                    
            elif exchange == "binance":
                async with binance_session.post(
                    BINANCE_ENDPOINT,
                    headers=BINANCE_HEADERS,
                    params=params,
                    timeout=0.5  # Aggressive timeout for HFT
                ) as response:
                    data = await response.json(loads=orjson.loads)
                    if "clientOrderId" in data:
                        return data
                    last_error = data.get("msg", "Unknown Binance error")
            
            retries += 1
            await asyncio.sleep(0)  # Yield event loop but no delay
            
        except aiohttp.ClientError as e:
            last_error = f"Network error: {str(e)}"
            retries += 1
            await asyncio.sleep(0)
            
        except Exception as e:
            last_error = f"Critical error: {str(e)}"
            break  # Don't retry on unknown errors

    logger.error(f"Order failed after {max_retries} attempts: {last_error}")
    return None

async def bybit_price_stream():
    while True:
        try:
            async with bybit_session.ws_loop:
                await bybit_session.ws_loop.send(json.dumps({
                    "op": "subscribe",
                    "args": ["tickers.ADAUSDT"]
                }))
                async for msg in bybit_session.ws_loop:
                    if 'topic' in msg and 'tickers.ADAUSDT' in msg['topic']:
                        last_price = int(float(msg['data']['lastPrice']) * PRICE_MULTIPLIER)
                        prices["bybit"] = last_price
                        try:
                            evaluation_queue.put_nowait(None)
                        except asyncio.QueueFull:
                            evaluation_queue.get_nowait()
                            evaluation_queue.put_nowait(None)
        except Exception as e:
            logger.error(f"Bybit WS Error: {e}")
            await asyncio.sleep(5)

async def binance_price_stream():
    while True:
        try:
            stream = binance_ws.get_stream_signal()
            if binance_ws.is_manager_stopping():
                break
            data = binance_ws.pop_stream_data_from_stream_buffer(stream)
            if data and 'event_type' in data and data['event_type'] == '24hrTicker':
                last_price = int(float(data['close_price']) * PRICE_MULTIPLIER)
                prices["binance"] = last_price
                try:
                    evaluation_queue.put_nowait(None)
                except asyncio.QueueFull:
                    evaluation_queue.get_nowait()
                    evaluation_queue.put_nowait(None)
        except Exception as e:
            logger.error(f"Binance WS Error: {e}")
            await asyncio.sleep(5)

def closeLS(position,diff):

    qtyToClose = int(open_trades_LS[position]['cnt'])

    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Executing Close Orders LS: Bybit={prices['bybit'] / PRICE_MULTIPLIER:.4f}, Binance={prices['binance'] / PRICE_MULTIPLIER:.4f}, qtyToClose = {qtyToClose}")
    open_trades_snapshot = ", ".join(f"{k / DIFF_MULTIPLIER:.2f}" for k in sorted(open_trades_LS))
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Open trades LS snapshot {open_trades_snapshot}")

    # Close positions Binance
    asyncio.create_task(place_order("binance",{"symbol": "ADAUSDT", "side": "SELL","position" : "LONG", "quantity": qtyToClose}))  # Close Binance long position
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Binance Close Long on {prices['binance']} with close diff {diff} open diff {position}")
    # Open same position
    asyncio.create_task(place_order("binance",{"symbol": "ADAUSDT", "side": "BUY","position" : "LONG", "quantity": qtyToClose}))  # Open Binance long position
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Binance Open Long on {prices['binance']} with open diff {diff}")

    # Close positions ByBit
    asyncio.create_task(place_order("bybit", {"symbol": "ADAUSDT", "side": "Buy","position": 2, "qty": qtyToClose})) # Close bybit short 
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} ByBit Close Short on {prices['bybit']} with close diff {diff} open diff {position}")
    # Open same position
    asyncio.create_task(place_order("bybit", {"symbol": "ADAUSDT", "side": "Sell","position": 2, "qty": qtyToClose}))  # Open bybit short
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} ByBit Open Short on {prices['bybit']} with open diff {diff}")

    # Close profit entry
    open_trades_LS[position]['cnt'] =- qtyToClose

    # Add new entry
    current_entry  = open_trades_LS.get(diff, {diff: diff, 'cnt': 0})
    current_entry['cnt'] =+ qtyToClose
    open_trades_LS[diff] = current_entry

def closeSL(position,diff):
    qtyToClose = int(open_trades_LS[position]['cnt'])
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Executing Close Orders SL: Bybit={prices['bybit'] / PRICE_MULTIPLIER:.4f}, Binance={prices['binance'] / PRICE_MULTIPLIER:.4f}, qtyToClose = {qtyToClose}")
    open_trades_snapshot = ", ".join(f"{k / DIFF_MULTIPLIER:.2f}" for k in sorted(open_trades_LS))
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Open trades SL snapshot {open_trades_snapshot}")

    # Close positions Binance
    asyncio.create_task(place_order("binance",{"symbol": "ADAUSDT", "side": "BUY","position" : "SHORT", "quantity": QTY}))  # Close Binance long position
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Binance Close Short on {prices['binance']} with close diff {diff} open diff {position}")
    # Open same position
    asyncio.create_task(place_order("binance",{"symbol": "ADAUSDT", "side": "SELL","position" : "SHORT", "quantity": QTY}))  # Open Binance long position
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Binance Open Short on {prices['binance']} with open diff {diff}")

    # Close positions ByBit
    asyncio.create_task(place_order("bybit", {"symbol": "ADAUSDT", "side": "Sell","position": 1, "qty": QTY})) # Close bybit short 
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} ByBit Close Long on {prices['bybit']} with close diff {diff} open diff {position}")
    # Open same position
    asyncio.create_task(place_order("bybit", {"symbol": "ADAUSDT", "side": "Buy","position": 1, "qty": QTY}))  # Open bybit short
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} ByBit Open Long on {prices['bybit']} with open diff {diff}")

    # Close profit entry
    open_trades_SL[position]['cnt'] =- qtyToClose

    # Add new entry
    current_entry  = open_trades_SL.get(diff, {diff: diff, 'cnt': 0})
    current_entry['cnt'] =+ qtyToClose
    open_trades_LS[diff] = current_entry

def openPos(diff):
    # Opening new trades
    asyncio.create_task(place_order("binance",{"symbol": "ADAUSDT", "side": "BUY","position" : "LONG", "quantity": QTY}))  # Open Binance long position
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Binance Open Long on {prices['binance']} with open diff {diff}")
    asyncio.create_task(place_order("binance",{"symbol": "ADAUSDT", "side": "SELL","position" : "SHORT", "quantity": QTY}))  # Open Binance long position
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} Binance Open Short on {prices['binance']} with open diff {diff}")
    asyncio.create_task(place_order("bybit", {"symbol": "ADAUSDT", "side": "Sell","position": 2, "qty": QTY}))  # Open bybit short
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} ByBit Open Short on {prices['bybit']} with open diff {diff}")
    asyncio.create_task(place_order("bybit", {"symbol": "ADAUSDT", "side": "Buy","position": 1, "qty": QTY}))  # Open bybit short
    logger.info(f"{datetime.now().strftime('%m-%d %H:%M:%S.')}{str(datetime.now().microsecond)[:3]} ByBit Open Long on {prices['bybit']} with open diff {diff}")

    # Add positions to LS and SL
    current_entry  = open_trades_LS.get(diff, {diff: diff, 'cnt': 0})
    current_entry['cnt'] =+ QTY
    open_trades_LS[diff] = current_entry

    current_entry  = open_trades_SL.get(diff, {diff: diff, 'cnt': 0})
    current_entry['cnt'] =+ QTY
    open_trades_LS[diff] = current_entry


async def evaluation_consumer():
    while True:
        await evaluation_queue.get()
        async with evaluate_lock:
            if prices["binance"] == 0 or prices["bybit"] == 0:
                continue
            p1, p2 = prices["binance"], prices["bybit"]
            diff = ((p1 - p2) * 100 * PRICE_MULTIPLIER) // p1
            diff = diff // (PRICE_MULTIPLIER // DIFF_MULTIPLIER)
            
        ###################
        ###################
        ###################
        ###PRIVATE LOGIC###
        ###################
        ###################
        ###################

        evaluation_queue.task_done()
    
async def main():
    tasks = [
        asyncio.create_task(bybit_price_stream()),
        asyncio.create_task(binance_price_stream()),
        asyncio.create_task(evaluation_consumer()),
        asyncio.create_task(calcPosToClose(open_trades_LS,open_trades_SL))
    ]
    await asyncio.gather(*tasks)

if __name__ == "_main_":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        listener.stop()
        logger.info("Exiting...")