# -*- coding: utf-8 -*-
"""Trade Simulator Backend (Python - Port 8000)

Automatically generated by Colab.


"""

# Trade Simulator Backend (Python - Port 8000 v2.2)
# This script provides a more complete backend structure based on previous discussions.
# IMPORTANT:
# 1. Financial models (slippage, market impact) are SIMPLIFIED PLACEHOLDERS.
#    They are NOT calibrated for real-world use and should NOT be used for actual trading.
# 2. Connection to OKX WebSocket may require VPN and specific API handling.
# 3. This is a conceptual script and would need significant development for production use.

import asyncio
import websockets
import json
import time
import logging
import numpy as np
from datetime import datetime

# --- Configuration ---
# More verbose logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s'
)

# OKX WebSocket Endpoint for L2 Order Book data
OKX_L2_ENDPOINT = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"

# WebSocket Server for UI communication
UI_WEBSOCKET_HOST = "localhost"
UI_WEBSOCKET_PORT = 8000 # Port for UI to connect to

# --- Global State ---
current_order_book = {
    'bids': [], 'asks': [], 'timestamp': None, 'symbol': None, 'okx_ts': None
}
simulation_params = {
    'spot_asset': 'BTC-USDT-SWAP',
    'order_type': 'market',
    'quantity_usd': 1000.0,
    'volatility_pct': 60.0,
    'fee_tier_data': {'maker': 0.0008, 'taker': 0.0010},
    'average_daily_volume_asset': 50000.0
}

# Placeholders for actual trained models
slippage_model = None
maker_taker_model = None

# --- Model Functions (Simplified Placeholders) ---
def calculate_expected_slippage(order_book, asset_quantity, mid_price, params):
    """CONCEPTUAL/SIMPLIFIED: Calculates expected slippage."""
    if not order_book['asks'] or not order_book['bids'] or mid_price == 0:
        return 0.0
    try:
        best_ask_qty = float(order_book['asks'][0][1])
    except (IndexError, ValueError, TypeError):
        # Default slippage if book data is malformed
        return mid_price * 0.001 * asset_quantity

    slippage_factor = 0.0005 # Base slippage factor (0.05%)
    if best_ask_qty > 0 and asset_quantity > best_ask_qty:
        slippage_factor += (asset_quantity / best_ask_qty) * 0.001 # Additional 0.1%
    return mid_price * slippage_factor * asset_quantity

def calculate_expected_fees(quantity_usd, params):
    """Calculates fees based on taker rate for market orders."""
    if params['order_type'] == 'market':
        taker_rate = params['fee_tier_data'].get('taker', 0.001) # Default if not found
        return quantity_usd * taker_rate
    return 0.0 # Placeholder for non-market orders

def calculate_market_impact(order_book, asset_quantity, quantity_usd, mid_price, params):
    """CONCEPTUAL/SIMPLIFIED: Calculates expected market impact."""
    if mid_price == 0: return 0.0
    annualized_volatility_decimal = params['volatility_pct'] / 100.0
    adv_asset = params['average_daily_volume_asset']
    if adv_asset == 0: return 0.0

    daily_volatility = annualized_volatility_decimal / np.sqrt(252)
    impact_coefficient = 0.5  # NEEDS CALIBRATION
    size_exponent = 0.6       # NEEDS CALIBRATION

    if asset_quantity < 0: asset_quantity = 0
    relative_size = asset_quantity / adv_asset

    if relative_size > 0.1: # Cap relative size to avoid extreme impact
        relative_size = 0.1
        logging.debug(f"Order size ({asset_quantity}) large vs ADV ({adv_asset}). Capping relative_size.")

    price_impact_percentage = impact_coefficient * daily_volatility * (relative_size ** size_exponent)
    return quantity_usd * max(0, price_impact_percentage) # Ensure non-negative impact

def get_maker_taker_proportion(params):
    """Determines Maker/Taker proportion. For market orders, it's 100% Taker."""
    if params['order_type'] == 'market':
        return {"taker_pct": 100.0, "maker_pct": 0.0}
    # Placeholder for limit orders (would involve a model)
    return {"taker_pct": 0.0, "maker_pct": 0.0}

# --- WebSocket Handlers ---
connected_ui_clients = set()

async def ui_communication_handler(websocket, path=None):
    """Handles WebSocket connections from the Frontend UI."""
    global simulation_params
    client_address = websocket.remote_address
    connected_ui_clients.add(websocket)
    logging.info(f"UI Client connected: {client_address}")
    try:
        async for message in websocket:
            try:
                ui_data = json.loads(message)
                logging.info(f"Received from UI ({client_address}): {ui_data}")

                # Update simulation_params based on UI input
                if 'quantityUSD' in ui_data:
                    simulation_params['quantity_usd'] = float(ui_data['quantityUSD'])
                if 'volatility' in ui_data:
                    simulation_params['volatility_pct'] = float(ui_data['volatility'])
                if 'fee_tier_data' in ui_data:
                    if isinstance(ui_data['fee_tier_data'], dict) and \
                       'maker' in ui_data['fee_tier_data'] and \
                       'taker' in ui_data['fee_tier_data']:
                        simulation_params['fee_tier_data'] = ui_data['fee_tier_data']
                    else:
                        logging.warning(f"Malformed 'fee_tier_data' from UI: {ui_data['fee_tier_data']}")
                logging.info(f"Updated simulation_params: {simulation_params}")

            except json.JSONDecodeError:
                logging.error(f"Invalid JSON from UI ({client_address}). Msg: {message[:200]}")
            except Exception as e:
                logging.error(f"Error processing UI msg from {client_address}: {e}", exc_info=True)
    except websockets.exceptions.ConnectionClosed as e:
        logging.info(f"UI Client {client_address} disconnected. Code: {e.code}, Reason: {e.reason}")
    except Exception as e:
        logging.error(f"Unexpected error in UI handler for {client_address}: {e}", exc_info=True)
    finally:
        if websocket in connected_ui_clients: # Check if still present before removing
            connected_ui_clients.remove(websocket)
        logging.info(f"UI Client {client_address} removed from active connections.")

async def broadcast_to_ui(data_to_send):
    """Broadcasts processed data to all connected UI clients."""
    if connected_ui_clients:
        message_json = json.dumps(data_to_send)
        # Create a list of tasks for sending messages to avoid issues if the set changes during iteration
        tasks = [client.send(message_json) for client in list(connected_ui_clients)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # This mapping back to client can be tricky if the client set changed.
                # For simplicity, just log the error.
                logging.error(f"Error sending to a UI client: {result}")


async def okx_market_data_listener():
    """Connects to OKX L2 order book stream, processes data, and broadcasts to UI."""
    global current_order_book
    uri = OKX_L2_ENDPOINT

    while True: # Outer loop for retrying connection
        logging.info(f"Attempting to connect to OKX L2 feed: {uri}")
        try:
            # ping_interval and ping_timeout help maintain the connection
            async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as websocket:
                logging.info(f"Successfully connected to OKX L2 feed: {uri}")

                # OPTIONAL: Send subscription message if the URL doesn't auto-subscribe.
                # Verify the correct channel name and instId with OKX documentation.
                # Example: 'books5' for 5 levels of depth.
                # subscribe_msg = {
                #     "op": "subscribe",
                #     "args": [{"channel": "books5", "instId": simulation_params['spot_asset']}]
                # }
                # await websocket.send(json.dumps(subscribe_msg))
                # logging.info(f"Sent subscription request to OKX: {subscribe_msg}")

                async for message_raw in websocket:
                    tick_processing_start_time = time.perf_counter()
                    try:
                        message_data = json.loads(message_raw)
                        # logging.debug(f"Raw from OKX: {message_data}")

                        # Handle OKX Ping/Pong (OKX v5 API sends "ping" as a string)
                        if isinstance(message_data, str) and message_data == "ping":
                            await websocket.send("pong")
                            logging.debug("Sent PONG to OKX (string format)")
                            continue
                        # Handle other exchanges' op:ping format if necessary
                        if isinstance(message_data, dict) and message_data.get("op") == "ping":
                             await websocket.send(json.dumps({"op": "pong"}))
                             logging.debug("Sent PONG to OKX (op format)")
                             continue

                        # Handle subscription responses and errors
                        if isinstance(message_data, dict) and "event" in message_data:
                            if message_data["event"] == "subscribe":
                                logging.info(f"OKX: Successfully subscribed: {message_data.get('arg')}")
                                continue
                            if message_data["event"] == "error":
                                logging.error(f"OKX WS Error: Code {message_data.get('code')}, Msg: {message_data.get('msg')}")
                                # If critical error (e.g., auth, invalid args), break inner loop to force reconnect
                                if message_data.get('code') in ['60008', '60013', '60014']:
                                    logging.error("OKX: Critical subscription/auth error. Breaking connection loop.")
                                    break
                                continue

                        data_payload = None
                        action = None
                        # Adapt to common OKX L2 structure or the simpler prompt structure
                        if "data" in message_data and isinstance(message_data["data"], list) and message_data["data"]:
                            data_payload = message_data["data"][0] # Data is usually an array with one object
                            action = message_data.get("action", "update") # Default to "update" if action not present
                        elif "asks" in message_data and "bids" in message_data : # Fallback to simpler format from prompt
                             data_payload = message_data
                             action = "snapshot" # Treat as a full snapshot

                        if not data_payload:
                            logging.debug(f"OKX: No usable data_payload in message: {message_raw[:200]}")
                            continue

                        # Update order book (simplified: treat updates as snapshots)
                        if action == "snapshot" or action == "update":
                            current_order_book['asks'] = data_payload.get('asks', [])
                            current_order_book['bids'] = data_payload.get('bids', [])
                            current_order_book['okx_ts'] = data_payload.get('ts', current_order_book['okx_ts']) # OKX uses 'ts' (milliseconds string)
                            current_order_book['symbol'] = simulation_params['spot_asset'] # Assuming one symbol for now
                            if not current_order_book['asks'] and not current_order_book['bids']:
                                logging.debug("OKX: Received empty asks/bids in snapshot/update.")
                                continue # No data to process
                        else:
                            logging.warning(f"OKX: Unknown action '{action}' or no relevant data fields: {message_raw[:200]}")
                            continue

                        # --- Core Processing Logic after order book update ---
                        if not current_order_book['bids'] or not current_order_book['asks']:
                            logging.debug("Order book is empty or incomplete after update, skipping calculations.")
                            continue

                        try:
                            best_bid_price = float(current_order_book['bids'][0][0])
                            best_ask_price = float(current_order_book['asks'][0][0])
                        except (IndexError, ValueError, TypeError) as e:
                            logging.warning(f"Could not extract best bid/ask from order book: {e}. Book state: Asks: {current_order_book['asks'][:1]}, Bids: {current_order_book['bids'][:1]}")
                            continue # Skip this tick if book is malformed

                        mid_price = (best_bid_price + best_ask_price) / 2.0
                        if mid_price == 0:
                            logging.warning("Mid price is zero, skipping calculations.")
                            continue

                        asset_quantity = simulation_params['quantity_usd'] / mid_price

                        # Call model functions
                        slippage_usd = calculate_expected_slippage(current_order_book, asset_quantity, mid_price, simulation_params)
                        fees_usd = calculate_expected_fees(simulation_params['quantity_usd'], simulation_params)
                        impact_usd = calculate_market_impact(current_order_book, asset_quantity, simulation_params['quantity_usd'], mid_price, simulation_params)
                        net_cost_usd = slippage_usd + fees_usd + impact_usd
                        maker_taker_info = get_maker_taker_proportion(simulation_params)

                        tick_processing_end_time = time.perf_counter()
                        processing_latency_ms = (tick_processing_end_time - tick_processing_start_time) * 1000

                        # Prepare data for UI
                        iso_timestamp = "N/A"
                        if current_order_book.get('okx_ts'):
                            try:
                                ts_int = int(current_order_book['okx_ts'])
                                # Convert milliseconds to seconds for utcfromtimestamp
                                iso_timestamp = datetime.utcfromtimestamp(ts_int / 1000).isoformat() + 'Z'
                            except (ValueError, TypeError):
                                logging.warning(f"Could not parse OKX timestamp: {current_order_book['okx_ts']}")

                        output_for_ui = {
                            "bestBid": best_bid_price, "bestAsk": best_ask_price,
                            "midPrice": round(mid_price, 2),
                            "expectedSlippage": round(slippage_usd, 2),
                            "expectedFees": round(fees_usd, 2),
                            "marketImpact": round(impact_usd, 2),
                            "netCost": round(net_cost_usd, 2),
                            "makerTaker": f"Taker: {maker_taker_info['taker_pct']:.0f}%, Maker: {maker_taker_info['maker_pct']:.0f}%",
                            "internalLatency": round(processing_latency_ms, 2),
                            "lastUpdate": iso_timestamp,
                            "asks": current_order_book['asks'][:5], # Send top 5 levels to UI
                            "bids": current_order_book['bids'][:5]
                        }
                        await broadcast_to_ui(output_for_ui)

                    except json.JSONDecodeError:
                        logging.warning(f"OKX: Failed to decode JSON from message: {message_raw[:200]}")
                    except Exception as e: # Catch-all for the inner message processing loop
                        logging.error(f"OKX: Error processing message: {e}", exc_info=True)

        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"OKX: ConnectionClosedError: {e}. Server may have forcefully closed. Retrying...")
        except websockets.exceptions.ConnectionClosed as e:
            logging.warning(f"OKX: WebSocket connection closed: {e}. Code: {e.code}. Reason: {e.reason}. Retrying...")
        except ConnectionRefusedError:
            logging.error("OKX: Connection refused. Check network/VPN and endpoint URL. Retrying...")
        except asyncio.TimeoutError: # Catch specific timeout errors if connect takes too long
            logging.error("OKX: Connection attempt timed out. Retrying...")
        except Exception as e: # Catch-all for the connection loop
            logging.error(f"OKX: Unexpected error in WebSocket connection loop: {e}", exc_info=True)

        logging.info("Waiting 10 seconds before retrying OKX connection...")
        await asyncio.sleep(10) # Wait before retrying connection

async def main_backend_loop():
    """Main function to start the backend services."""
    # Start the WebSocket server for UI clients
    server = await websockets.serve(ui_communication_handler, UI_WEBSOCKET_HOST, UI_WEBSOCKET_PORT)
    logging.info(f"UI WebSocket server started on ws://{UI_WEBSOCKET_HOST}:{UI_WEBSOCKET_PORT}")

    # Start the listener for OKX market data
    okx_task = asyncio.create_task(okx_market_data_listener())

    try:
        # Keep the tasks running. If okx_task finishes or errors,
        # this gather will complete/raise. The server runs indefinitely until closed.
        await asyncio.gather(okx_task)
    except KeyboardInterrupt:
        logging.info("Backend shutting down by user interrupt (main_backend_loop)...")
    except Exception as e:
        logging.critical(f"Critical error in main_backend_loop gather: {e}", exc_info=True)
    finally:
        logging.info("Main backend loop ending. Cleaning up...")
        if okx_task and not okx_task.done():
            logging.info("Cancelling OKX listener task...")
            okx_task.cancel()
            try:
                await okx_task # Allow task to process cancellation
            except asyncio.CancelledError:
                logging.info("OKX listener task successfully cancelled.")
            except Exception as e_cancel: # Catch any error during cancellation
                logging.error(f"Error during OKX task cancellation: {e_cancel}", exc_info=True)

        if server: # Close the UI server
            server.close()
            await server.wait_closed()
            logging.info("UI WebSocket server closed.")
        logging.info("Backend shutdown sequence complete.")

if __name__ == "__main__":
    logging.info("Starting Trade Simulator Backend (Port 8000 v2.2)...")
    try:
        # Get the current event loop.
        # In some environments (like Jupyter/IPython), a loop might already be running.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None

        if loop and loop.is_running():
            logging.info("Asyncio event loop is already running. Scheduling main_backend_loop as a task.")
            # If a loop is already running (e.g., in Jupyter), create a task for the main coroutine.
            task = loop.create_task(main_backend_loop())
            # In a Jupyter notebook, this task will run in the background.
            # To wait for it in a cell, you might need `await task` if the cell is async.
        else:
            logging.info("No running asyncio event loop found or loop is None. Starting new one with asyncio.run().")
            asyncio.run(main_backend_loop())

    except KeyboardInterrupt:
        logging.info("Backend process interrupted by user at startup (KeyboardInterrupt).")
    except RuntimeError as e:
        # This specific check might be redundant now with the logic above, but kept for safety.
        if "cannot be called from a running event loop" in str(e):
            logging.error(
                "FATAL: asyncio.run() was called from an already running event loop. "
                "This indicates an issue with how the script is being launched in this environment. "
                "The script attempted to handle this, but the error still occurred. "
                "If in Jupyter/IPython, try running 'await main_backend_loop()' in an async cell."
            )
        else: # Log other RuntimeErrors
            logging.critical(f"A RuntimeError occurred at startup: {e}", exc_info=True)
    except Exception as e: # Catch any other exceptions during startup
        logging.critical(f"An unexpected error occurred at startup: {e}", exc_info=True)