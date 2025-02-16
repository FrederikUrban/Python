#MODIFY PRICE TO INT
import asyncio
import logging
import uvloop
import orjson  # Fast JSON parsing
from collections import deque
from unicorn_binance_websocket_api import BinanceWebSocketApiManager
from pybit.unified_trading import WebSocket as BybitWebSocket

# Use uvloop for better performance on Linux
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Constants
ORDER_QTY = 15  # (if needed for order sizing later)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Queues for storing the latest prices (only one item is kept)
binance_price_queue = deque(maxlen=1)
bybit_price_queue = deque(maxlen=1)


async def process_binance_price(price_queue: deque):
    """
    Consumer function: Process and print only the newest Binance price.
    This loop flushes the queue to ensure only the most recent price is processed.
    """
    while True:
        if price_queue:
            latest_price = None
            # Flush the queue and keep only the last update.
            while price_queue:
                latest_price = price_queue.popleft()
            if latest_price is not None:
                print(f"Latest Binance Price: {latest_price}")
        await asyncio.sleep(0.001)  # Tiny delay to yield control


async def process_bybit_price(price_queue: deque):
    """
    Consumer function: Process and print only the newest Bybit price.
    This loop flushes the queue to ensure only the most recent price is processed.
    """
    while True:
        if price_queue:
            latest_price = None
            while price_queue:
                latest_price = price_queue.popleft()
            if latest_price is not None:
                print(f"Latest Bybit Price: {latest_price}")
        await asyncio.sleep(0.001)  # Tiny delay to yield control


async def handle_binance_stream(binance_websocket_manager: BinanceWebSocketApiManager):
    """
    Producer function: Process incoming Binance stream data.
    Uses orjson for faster JSON parsing and extracts the nested 'data' if present.
    """
    while True:
        try:
            stream_data = binance_websocket_manager.pop_stream_data_from_stream_buffer()
            if stream_data:
                # In some cases, the data might be in bytes; decode if needed.
                if isinstance(stream_data, bytes):
                    stream_data = stream_data.decode("utf-8")
                if isinstance(stream_data, str):
                    try:
                        # Use orjson for fast JSON decoding
                        stream_data = orjson.loads(stream_data)
                    except Exception as e:
                        logging.error(
                            f"Failed to decode JSON from Binance: {e}, data: {stream_data}",
                            exc_info=True
                        )
                        continue

                # If data is nested under "data", extract it.
                if "data" in stream_data:
                    stream_data = stream_data["data"]

                # Process markPriceUpdate events
                if stream_data.get("e") == "markPriceUpdate":
                    price = float(stream_data.get("p", 0))
                    binance_price_queue.append(price)
                elif "result" in stream_data and stream_data["result"] is None:
                    logging.info(f"Binance: Subscription confirmation: {stream_data}")
                else:
                    logging.warning(f"Unexpected Binance data format: {stream_data}")
        except Exception as e:
            logging.error(f"Error processing Binance data: {e}", exc_info=True)
        await asyncio.sleep(0.001)  # Tiny delay to prevent busy-waiting


async def handle_bybit_stream(bybit_ws: BybitWebSocket):
    """
    Producer function: Process incoming Bybit stream data.
    Registers a callback that appends the latest price to the queue.
    """
    def on_message(message):
        try:
            # Check for expected topic and ensure 'data' is present
            if message and message.get("topic") == "tickers.ADAUSDT" and "data" in message:
                price = float(message["data"].get("lastPrice", 0))
                bybit_price_queue.append(price)
            elif message:
                logging.warning(f"Unexpected Bybit data format: {message}")
        except Exception as e:
            logging.error(f"Error processing Bybit data: {e}", exc_info=True)

    # Register the callback for the ticker stream (note: singular 'ticker_stream')
    bybit_ws.ticker_stream(symbol="ADAUSDT", callback=on_message)

    # Keep the connection alive with a minimal sleep loop
    while True:
        await asyncio.sleep(0.001)


async def main():
    """Main function: Initialize WebSocket managers and run the producer/consumer tasks."""
    # Instantiate and set up the Binance WebSocket Manager
    binance_websocket_manager = BinanceWebSocketApiManager(exchange="binance.com-futures")
    binance_websocket_manager.create_stream(
        channels=['markPrice'],
        markets=['adausdt'],
        stream_label="adausdt_markPrice"
    )

    # Instantiate the Bybit WebSocket
    bybit_ws = BybitWebSocket(
        testnet=False,
        channel_type="linear",
    )

    # Create tasks for handling streams and processing prices
    binance_task = asyncio.create_task(handle_binance_stream(binance_websocket_manager))
    bybit_task = asyncio.create_task(handle_bybit_stream(bybit_ws))
    binance_consumer_task = asyncio.create_task(process_binance_price(binance_price_queue))
    bybit_consumer_task = asyncio.create_task(process_bybit_price(bybit_price_queue))

    try:
        # Run all tasks concurrently
        await asyncio.gather(
            binance_task,
            bybit_task,
            binance_consumer_task,
            bybit_consumer_task
        )
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        logging.info("Shutting down WebSocket connections.")
        if bybit_ws:
            bybit_ws.exit()
        if binance_websocket_manager:
            binance_websocket_manager.stop_manager_with_all_streams()

if __name__ == "__main__":
    asyncio.run(main())
