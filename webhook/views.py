from django.shortcuts import render


import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Dummy webhook to simulate receiving signals without executing trades
@csrf_exempt
def tradingview_webhook(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)

            # Extract key data points from TradingView
            symbol = data.get('symbol')
            signal = data.get('signal')

            # Log the received data for debugging purposes
            logging.info(f"Received signal: {signal} for symbol: {symbol}")

            # Return a dummy success response
            return JsonResponse({'status': 'success', 'message': f'Received signal: {signal} for {symbol}'})

        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from TradingView.")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        
        except Exception as e:
            logging.error(f"Error processing webhook: {e}")
            return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)
    
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# # Create your views here.
# import json
# import logging
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# import MetaTrader5 as mt5

# # Initialize logging
# logging.basicConfig(level=logging.INFO)

# # Disable CSRF for the webhook endpoint
# @csrf_exempt
# def tradingview_webhook(request):
#     if request.method == 'POST':
#         try:
#             # Parse incoming JSON data
#             data = json.loads(request.body)
            
#             # Extract key data points from TradingView
#             symbol = data.get('symbol')
#             signal = data.get('signal')

#             # Validate the incoming data
#             if not symbol or not signal:
#                 logging.error("Invalid data received from TradingView.")
#                 return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

#             # Log in to MT5
#             if not mt5.initialize():
#                 logging.error("Failed to initialize MT5.")
#                 return JsonResponse({'status': 'error', 'message': 'MT5 initialization failed'}, status=500)

#             account_number = 12345678  # Replace with your MT5 account number
#             password = 'password'  # Replace with your MT5 password
#             if not mt5.login(account_number, password):
#                 logging.error("Failed to log in to MT5 account.")
#                 return JsonResponse({'status': 'error', 'message': 'MT5 login failed'}, status=500)

#             # Determine order type based on signal (BUY/SELL)
#             if signal.upper() == 'BUY':
#                 order_type = mt5.ORDER_TYPE_BUY
#             elif signal.upper() == 'SELL':
#                 order_type = mt5.ORDER_TYPE_SELL
#             else:
#                 logging.error("Invalid signal type received.")
#                 return JsonResponse({'status': 'error', 'message': 'Invalid signal type'}, status=400)

#             # Prepare the trade request
#             request = {
#                 "action": mt5.TRADE_ACTION_DEAL,
#                 "symbol": symbol,
#                 "volume": 0.1,  # Set your desired volume
#                 "type": order_type,
#                 "price": mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid,
#                 "deviation": 20,  # Price deviation (pips)
#                 "magic": 234000,  # Identifier for your bot
#                 "comment": f"TradingView {signal} signal",
#                 "type_time": mt5.ORDER_TIME_GTC,  # Good till canceled
#                 "type_filling": mt5.ORDER_FILLING_IOC,
#             }

#             # Execute the trade
#             result = mt5.order_send(request)

#             if result.retcode != mt5.TRADE_RETCODE_DONE:
#                 logging.error(f"Trade execution failed. Retcode: {result.retcode}")
#                 return JsonResponse({'status': 'error', 'message': f'Trade failed: {result.retcode}'}, status=500)

#             # Trade was successful
#             logging.info(f"Trade executed successfully: {result}")
#             return JsonResponse({'status': 'success', 'message': 'Trade executed successfully'})

#         except Exception as e:
#             logging.error(f"Error processing webhook: {e}")
#             return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)
#     else:
#         return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
