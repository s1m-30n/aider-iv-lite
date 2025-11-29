import time
import MetaTrader5 as mt5 # Needed for constants like ORDER_TYPE_BUY
from mt5_client import MT5Client
from strategy import Strategy

# Constants
SYMBOLS = [
    "Boom 500 Index", "Crash 500 Index",
    "Boom 600 Index", "Crash 600 Index",
    "Boom 900 Index", "Crash 900 Index",
    "Boom 1000 Index", "Crash 1000 Index"
]
TIMEFRAME = mt5.TIMEFRAME_M5 # Using M5 for now
VOLUME = 0.2 # Minimum lot size, adjust as needed

def main():
    print("Starting Aider Lite Bot...")
    
    client = MT5Client()
    if not client.initialize():
        print("Failed to initialize MT5 Client")
        return

    strategy = Strategy()
    
    try:
        while True:
            print(f"Scanning markets at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
            
            for symbol in SYMBOLS:
                # Get data
                df = client.get_data(symbol, TIMEFRAME, 100)
                if df.empty:
                    continue
                
                # Analyze
                signal = strategy.analyze_symbol(symbol, df)
                
                if signal:
                    print(f"Signal found for {symbol}: {signal['signal']} ({signal['type']})")
                    
                    # Check if we already have a position for this symbol
                    positions = client.get_open_positions(symbol=symbol)
                    if len(positions) == 0:
                        # Place order
                        order_type = mt5.ORDER_TYPE_BUY if signal['signal'] == 'buy' else mt5.ORDER_TYPE_SELL
                        
                        result = client.place_order(
                            symbol=symbol,
                            order_type=order_type,
                            volume=VOLUME,
                            sl=signal['sl'],
                            tp=signal['tp'],
                            comment=f"AiderLite {signal['type']}"
                        )
                        
                        if result:
                            print(f"Order placed for {symbol}: {result}")
                    else:
                        print(f"Position already exists for {symbol}, skipping.")
            
            # Manage trailing stops
            manage_trailing_stops(client)
            
            # Sleep for a bit (e.g., 1 minute)
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    finally:
        client.shutdown()

def manage_trailing_stops(client: MT5Client):
    """
    Simple trailing stop logic.
    If price moves in favor by X points, move SL to break even or trail.
    """
    positions = client.get_open_positions()
    if positions is None:
        return

    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        order_type = pos.type
        open_price = pos.price_open
        current_sl = pos.sl
        current_tp = pos.tp
        
        tick = client.get_symbol_tick(symbol)
        if tick is None:
            continue
            
        current_price = tick.bid if order_type == mt5.ORDER_TYPE_BUY else tick.ask
        
        # Calculate points in profit
        if order_type == mt5.ORDER_TYPE_BUY:
            profit_points = current_price - open_price
        else:
            profit_points = open_price - current_price
            
        # Example Trailing Logic (Placeholder)
        # print(f"Position {ticket} {symbol}: Profit {profit_points}")
        pass

if __name__ == "__main__":
    main()
