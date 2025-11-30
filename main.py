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
TIMEFRAMES = {
    'D1': mt5.TIMEFRAME_D1,
    'H4': mt5.TIMEFRAME_H4,
    'H1': mt5.TIMEFRAME_H1,
    'M15': mt5.TIMEFRAME_M15,
    'M5': mt5.TIMEFRAME_M5
}
VOLUME = 2 # Minimum lot size, adjust as needed

from ui import BotUI

def main():
    ui = BotUI()
    ui.print_banner()
    ui.log("Starting Aider Lite Bot...", "info")
    
    client = MT5Client()
    if not client.initialize():
        ui.log("Failed to initialize MT5 Client", "error")
        return

    strategy = Strategy()
    
    try:
        while True:
            # ui.log(f"Scanning markets...", "info")
            
            market_status = {}
            
            for symbol in SYMBOLS:
                # Get data for all timeframes
                data = {}
                missing_data = False
                for tf_name, tf_code in TIMEFRAMES.items():
                    # Fetch more candles for higher timeframes to ensure enough data for indicators (e.g. 200 EMA)
                    num_candles = 300 if tf_name == 'D1' else 100
                    df = client.get_data(symbol, tf_code, num_candles)
                    if df.empty:
                        ui.log(f"Failed to get {tf_name} data for {symbol}", "warning")
                        missing_data = True
                        break
                    data[tf_name] = df
                
                if missing_data:
                    continue
                
                # Analyze
                # Now returns (signal, details)
                signal, details = strategy.analyze_symbol(symbol, data)
                
                # Update Market Status for UI
                market_status[symbol] = details
                market_status[symbol]['signal'] = signal['signal'] if signal else 'None'
                
                if signal:
                    ui.log(f"Signal found for {symbol}: {signal['signal']} ({signal['type']})", "success")
                    
                    # Check if we already have a position for this symbol
                    positions = client.get_open_positions(symbol=symbol)
                    if len(positions) == 0:
                        # Place order
                        order_type = mt5.ORDER_TYPE_BUY if signal['signal'] == 'buy' else mt5.ORDER_TYPE_SELL
                        
                        # Alert User
                        ui.trade_alert(symbol, signal['signal'], signal['price'], signal['sl'], signal['tp'])
                        
                        result = client.place_order(
                            symbol=symbol,
                            order_type=order_type,
                            volume=VOLUME,
                            sl=signal['sl'],
                            tp=signal['tp'],
                            comment=f"AiderLite {signal['type']}"
                        )
                        
                        if result:
                            ui.log(f"Order placed for {symbol}: {result}", "success")
                    else:
                        ui.log(f"Position already exists for {symbol}, skipping.", "warning")
            
            # Print Status Table
            ui.print_status(market_status)
            
            # Manage active trades (Smart Exit)
            manage_active_trades(client, strategy, ui)
            
            # Sleep for a bit (e.g., 30 seconds)
            time.sleep(30)
            
    except KeyboardInterrupt:
        ui.log("Bot stopped by user.", "warning")
    finally:
        client.shutdown()

def manage_active_trades(client: MT5Client, strategy: Strategy, ui: BotUI):
    """
    Manage open positions:
    1. Smart Exit: Close if Profit > $0.50 AND Spike Risk is High (>70%).
    2. Trailing Stop: (Optional/Future)
    """
    positions = client.get_open_positions()
    if positions is None:
        return

    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        profit = pos.profit # Profit in account currency (e.g., USD)
        
        # 1. Get M5 data for Spike Prediction
        df_m5 = client.get_data(symbol, mt5.TIMEFRAME_M5, 100)
        if df_m5 is None or df_m5.empty:
            continue
            
        # 2. Predict Spike
        spike_pred = strategy.predict_spike(symbol, df_m5)
        spike_prob = spike_pred['probability'] if spike_pred else 0.0
        
        # 3. Smart Exit Rule
        # Close if Spike Risk is High (>= 70%) AND the spike is against our position.
        # Boom Spikes = UP (Bad for Sell)
        # Crash Spikes = DOWN (Bad for Buy)
        
        is_boom = "Boom" in symbol
        is_crash = "Crash" in symbol
        is_buy = pos.type == mt5.ORDER_TYPE_BUY
        is_sell = pos.type == mt5.ORDER_TYPE_SELL
        
        should_close = False
        
        if spike_prob >= 70:
            if is_boom and is_sell:
                should_close = True
                reason = f"High Spike Risk ({spike_prob}%) on Boom (Sell Position)"
            elif is_crash and is_buy:
                should_close = True
                reason = f"High Spike Risk ({spike_prob}%) on Crash (Buy Position)"
                
        if should_close:
            ui.log(f"🚨 Smart Exit Triggered for {symbol} (Ticket {ticket})", "warning")
            ui.log(f"   Reason: {reason}", "warning")
            
            # Close Position
            if client.close_position(ticket):
                ui.log(f"   ✅ Trade Closed Successfully.", "success")
            else:
                ui.log(f"   ❌ Failed to Close Trade.", "error")
        
        # Logging for monitoring
        elif profit > 0.5:
             ui.log(f"👀 Monitoring {symbol}: Profit ${profit:.2f}, Spike Risk {spike_prob}% (Safe)", "info")

if __name__ == "__main__":
    main()
