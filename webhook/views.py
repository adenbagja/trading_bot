import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import MetaTrader5 as mt5

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Disable CSRF for the webhook endpoint
@csrf_exempt
def tradingview_webhook(request):
    if request.method == 'POST':
        try:
            # Parse incoming JSON data
            data = json.loads(request.body)

            # Extract key data points from TradingView
            symbol = data.get('symbol')
            trade_type = data.get('signal')

            # Validate the incoming data
            if not symbol or not trade_type:
                logging.error("Invalid data received from TradingView.")
                return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

            # Establish connection to the MetaTrader 5 terminal
            if not mt5.initialize():
                logging.error("MT5 initialization failed.")
                return JsonResponse({'status': 'error', 'message': 'MT5 initialization failed'}, status=500)

            try:
                # Fetch symbol info and price details
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is None:
                    logging.error(f"{symbol} not found, cannot call order_check()")
                    return JsonResponse({'status': 'error', 'message': f'Symbol {symbol} not found'}, status=400)

                if not symbol_info.visible:
                    if not mt5.symbol_select(symbol, True):
                        logging.error(f"symbol_select({symbol}) failed")
                        return JsonResponse({'status': 'error', 'message': f'Failed to select symbol {symbol}'}, status=500)

                # Retrieve symbol tick data
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    logging.error(f"Failed to retrieve tick data for {symbol}")
                    return JsonResponse({'status': 'error', 'message': f'Failed to retrieve tick data for {symbol}'}, status=500)

                point = symbol_info.point
                lot = 0.01
                deviation = 20

                # Get minimum stops level (in points)
                stops_level = symbol_info.trade_stops_level * point  # Convert stops level to actual price points

                # Set minimum SL and TP distances in pips
                sl_distance = max(400 * point, stops_level)  # Use at least 20 pips or the minimum stops level
                tp_distance = max(1200 * point, stops_level)  # Use at least 80 pips or the minimum stops level

                # Determine whether it’s a buy or sell order
                if trade_type.upper() == 'BUY':
                    order_type = mt5.ORDER_TYPE_BUY
                    price = tick.ask
                    sl = price - sl_distance  # Stop-loss is below for a buy
                    tp = price + tp_distance  # Take-profit is above for a buy
                elif trade_type.upper() == 'SELL':
                    order_type = mt5.ORDER_TYPE_SELL
                    price = tick.bid
                    sl = price + sl_distance  # Stop-loss is above for a sell
                    tp = price - tp_distance  # Take-profit is below for a sell
                else:
                    logging.error("Invalid trade type received.")
                    return JsonResponse({'status': 'error', 'message': 'Invalid trade type'}, status=400)

                # Prepare the trading request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": lot,
                    "type": order_type,
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "deviation": deviation,
                    "magic": 234000,
                    "comment": "python script open",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_FOK,
                }

                # Send the trading request
                result = mt5.order_send(request)

                # Check the execution result
                logging.info(f"order_send(): {trade_type} {symbol} {lot} lots at {price} with deviation={deviation} points")
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    logging.error(f"Order send failed, retcode={result.retcode}")
                    result_dict = result._asdict()
                    for field in result_dict.keys():
                        logging.error(f"   {field}={result_dict[field]}")
                    return JsonResponse({'status': 'error', 'message': f'Order execution failed, retcode={result.retcode}'}, status=500)

                # Return success response
                return JsonResponse({'status': 'success', 'message': f'{trade_type} order placed for {symbol} at {price} with SL={sl} and TP={tp}'})

            finally:
                # Shutdown MetaTrader 5 connection
                mt5.shutdown()

        except json.JSONDecodeError:
            logging.error("Invalid JSON received.")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)

        except Exception as e:
            logging.error(f"Error processing webhook: {e}")
            return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)

    # Return method not allowed for non-POST requests
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
