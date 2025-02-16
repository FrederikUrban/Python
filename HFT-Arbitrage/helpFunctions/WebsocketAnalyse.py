#MODIFY PRICE TO INT
#!/usr/bin/env python3
import asyncio
import logging
import uvloop
import orjson  # Fast JSON parsing
import signal
from collections import deque
from time import strftime, gmtime
import time
import cProfile, pstats

from unicorn_binance_websocket_api import BinanceWebSocketApiManager
from pybit.unified_trading import WebSocket as BybitWebSocket

# Use uvloop for better performance on Linux
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

################# LOGS @@@@@@@@@@@#
outputPath = '/root/Log_' + str(strftime("%d_%m_%Y", gmtime())) + '.csv'
errorPath = '/root/ErrorLog_' + str(strftime("%d_%m_%Y", gmtime())) + '.csv'

# Configure the logger
logger = logging.getLogger('HFT')
logger.setLevel(logging.INFO)  # Capture INFO and above

# Remove any existing handlers
logger.handlers = []

# 1. Info File Handler (writes ONLY INFO logs to outputPath)
info_handler = logging.FileHandler(
    filename=outputPath,
    mode='a'  # Append mode
)
info_handler.addFilter(lambda record: record.levelno == logging.INFO)
info_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(info_handler)

# 2. Error File Handler (writes all logs excluding only INFO logs to errorPath)
error_handler = logging.FileHandler(
    filename=errorPath,
    mode='a'
)
error_handler.setLevel(logging.DEBUG)
error_handler.addFilter(lambda record: record.levelno != logging.INFO)
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(error_handler)
################# END LOG CONFIG #############

# Global termination flag
exit_requested = False

# Constants
ORDER_QTY = 15  # (if needed for order sizing later)

# Queues for storing the latest prices (only one item is kept)
binance_price_queue = deque(maxlen=1)
bybit_price_queue = deque(maxlen=1)

async def process_binance_price(price_queue: deque):
    """
    Consumer: Process and print only the newest Binance price.
    (Price updates are printed to the console, not logged.)
    """
    while True:
        if price_queue:
            latest_price = None
            # Flush the queue to keep only the most recent price.
            while price_queue:
                latest_price = price_queue.popleft()
            if latest_price is not None:
                print(f"Latest Binance Price: {latest_price}")
        await asyncio.sleep(0.001)

async def process_bybit_price(price_queue: deque):
    """
    Consumer: Process and print only the newest Bybit price.
    (Price updates are printed to the console, not logged.)
    """
    while True:
        if price_queue:
            latest_price = None
            while price_queue:
                latest_price = price_queue.popleft()
            if latest_price is not None:
                print(f"Latest Bybit Price: {latest_price}")
        await asyncio.sleep(0.001)

async def handle_binance_stream(binance_websocket_manager: BinanceWebSocketApiManager):
    """
    Producer: Process incoming Binance stream data.
    Uses orjson for faster JSON parsing and extracts nested 'data' if present.
    Now subscribes to the ticker channel and prints lastPrice from field "c".
    """
    while True:
        try:
            stream_data = binance_websocket_manager.pop_stream_data_from_stream_buffer()
            if stream_data:
                # Decode bytes if necessary
                if isinstance(stream_data, bytes):
                    stream_data = stream_data.decode("utf-8")
                if isinstance(stream_data, str):
                    try:
                        stream_data = orjson.loads(stream_data)
                    except Exception as e:
                        logger.error(
                            f"Failed to decode JSON from Binance: {e}, data: {stream_data}",
                            exc_info=True
                        )
                        continue

                # If the event data is nested under "data", extract it.
                if "data" in stream_data:
                    stream_data = stream_data["data"]

                # Look for the 24hrTicker event which contains the last price in "c"
                if stream_data.get("e") == "24hrTicker":
                    price = float(stream_data.get("c", 0))
                    binance_price_queue.append(price)
                elif "result" in stream_data and stream_data["result"] is None:
                    logger.info(f"Binance: Subscription confirmation: {stream_data}")
                else:
                    logger.warning(f"Unexpected Binance data format: {stream_data}")
        except Exception as e:
            logger.error(f"Error processing Binance data: {e}", exc_info=True)
        await asyncio.sleep(0.001)

async def handle_bybit_stream(bybit_ws: BybitWebSocket):
    """
    Producer: Process incoming Bybit stream data.
    Registers a callback that appends the latest price to the queue.
    """
    def on_message(message):
        try:
            if message and message.get("topic") == "tickers.ADAUSDT" and "data" in message:
                price = float(message["data"].get("lastPrice", 0))
                bybit_price_queue.append(price)
            elif message:
                logger.warning(f"Unexpected Bybit data format: {message}")
        except Exception as e:
            logger.error(f"Error processing Bybit data: {e}", exc_info=True)

    # Note: using 'ticker_stream' (singular) as per the correct API method
    bybit_ws.ticker_stream(symbol="ADAUSDT", callback=on_message)

    while True:
        await asyncio.sleep(0.001)

def shutdown_handler():
    """
    Signal handler that cancels all running asyncio tasks and sets the exit flag.
    """
    global exit_requested
    logger.info("Shutdown signal received. Cancelling tasks.")
    exit_requested = True
    for task in asyncio.all_tasks():
        task.cancel()

async def main():
    """
    Main: Initialize WebSocket managers, register signal handlers, and run tasks.
    """
    # Register signal handlers for graceful shutdown (works on UNIX-like systems)
    loop = asyncio.get_running_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, shutdown_handler)

    # Instantiate and set up the Binance WebSocket Manager with ticker channel
    binance_websocket_manager = BinanceWebSocketApiManager(exchange="binance.com-futures")
    binance_websocket_manager.create_stream(
        channels=['ticker'],  # Changed from 'markPrice' to 'ticker'
        markets=['adausdt'],
        stream_label="adausdt_ticker"
    )

    # Instantiate the Bybit WebSocket
    bybit_ws = BybitWebSocket(
        testnet=False,
        channel_type="linear",
    )

    # Create tasks for handling streams and processing prices
    binance_consumer_task = asyncio.create_task(process_binance_price(binance_price_queue))
    bybit_consumer_task = asyncio.create_task(process_bybit_price(bybit_price_queue))
    binance_task = asyncio.create_task(handle_binance_stream(binance_websocket_manager))
    bybit_task = asyncio.create_task(handle_bybit_stream(bybit_ws))

    try:
        # Run all tasks concurrently until cancelled
        await asyncio.gather(
            binance_task,
            bybit_task,
            binance_consumer_task,
            bybit_consumer_task
        )
    except asyncio.CancelledError:
        logger.info("Tasks have been cancelled.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        logger.info("Shutting down WebSocket connections.")
        if bybit_ws:
            bybit_ws.exit()
        if binance_websocket_manager:
            binance_websocket_manager.stop_manager_with_all_streams()

if __name__ == "__main__":
    # Outer loop to restart the main function in case of unexpected errors.
    while not exit_requested:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received. Exiting.")
            break
        except Exception as e:
            logger.error(f"Main function terminated with error: {e}", exc_info=True)
            time.sleep(5)
    logger.info("Script terminated. You can now modify your code.")
