import MetaTrader5 as mt5
from mt5_client import MT5Client
import time

def test_place_order():
    print("Testing place_order function...")
    client = MT5Client()
    if not client.initialize():
        print("Failed to initialize MT5 Client")
        return

    symbol = "Boom 600 Index"
    volume = 0.2
    order_type = mt5.ORDER_TYPE_SELL
    
    # Get current price
    tick = client.get_symbol_tick(symbol)
    if tick is None:
        print(f"Failed to get tick for {symbol}")
        client.shutdown()
        return
        
    price = tick.bid
    print(f"Current Bid Price for {symbol}: {price}")
    
    # Set SL/TP (e.g., 2000 points away to be safe)
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Failed to get symbol info for {symbol}")
        client.shutdown()
        return
        
    # Set SL/TP based on user request (SL=10, TP=20)
    # Assuming 1.0 price unit = 1 pip for these indices
    digits = symbol_info.digits
    sl_dist = 10.0
    tp_dist = 20.0
    
    sl = price + sl_dist
    tp = price - tp_dist
    
    # Normalize prices (handled by client now, but good to show)
    sl = round(sl, digits)
    tp = round(tp, digits)
    
    print(f"Attempting to place SELL order: Volume={volume}, Price={price}, SL={sl}, TP={tp}")
    
    result = client.place_order(symbol, order_type, volume, sl, tp, "Test Order")
    
    if result:
        print("Order placed successfully!")
        print(f"Result: {result}")
    else:
        print("Order placement failed.")
        
    client.shutdown()

if __name__ == "__main__":
    test_place_order()
