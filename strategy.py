import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from indicators.rsi import calculate_rsi
from indicators.ema import calculate_ema
from indicators.bollinger import calculate_bollinger_bands
from indicators.macd import calculate_macd
from indicators.stochastic import calculate_stochastic
from indicators.atr import calculate_atr

class Strategy:
    def __init__(self):
        pass

    def analyze_symbol(self, symbol: str, df: pd.DataFrame) -> dict:
        """
        Analyze a symbol for trade opportunities.
        
        Args:
            symbol (str): The symbol to analyze.
            df (pd.DataFrame): Historical data.
            
        Returns:
            dict: Signal dictionary (e.g., {'signal': 'sell', 'type': 'scalp', 'sl': ..., 'tp': ...}) or None.
        """
        if df.empty:
            return None

        # Calculate indicators
        close_prices = df['close'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        
        rsi = calculate_rsi(close_prices)
        ema_50 = calculate_ema(close_prices, period=50)
        upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(close_prices)
        macd, macd_signal, macd_hist = calculate_macd(close_prices)
        slowk, slowd = calculate_stochastic(high_prices, low_prices, close_prices)
        atr = calculate_atr(high_prices, low_prices, close_prices)
        
        if len(rsi) == 0:
            return None

        current_price = close_prices[-1]
        current_rsi = rsi[-1]
        current_ema = ema_50[-1]
        current_upper_bb = upper_bb[-1]
        current_lower_bb = lower_bb[-1]
        current_macd = macd[-1]
        current_signal = macd_signal[-1]
        current_slowk = slowk[-1]
        current_slowd = slowd[-1]
        current_atr = atr[-1]

        signal = None
        trade_type = "scalp" # Default to scalp for now

        # Boom Logic (Sell Only)
        if "Boom" in symbol:
            # Condition 1: Price above Upper Bollinger Band
            # Condition 2: RSI Overbought (> 70)
            # Condition 3: Stochastic Overbought (> 80)
            if current_price > current_upper_bb and current_rsi > 70 and current_slowk > 80:
                 if current_slowk < slowk[-2]: # Stochastic crossing down
                    signal = "sell"
        
        # Crash Logic (Buy Only)
        elif "Crash" in symbol:
            # Condition 1: Price below Lower Bollinger Band
            # Condition 2: RSI Oversold (< 30)
            # Condition 3: Stochastic Oversold (< 20)
            if current_price < current_lower_bb and current_rsi < 30 and current_slowk < 20:
                if current_slowk > slowk[-2]: # Stochastic crossing up
                    signal = "buy"

        if signal:
            # Calculate SL/TP based on ATR
            sl_pips = current_atr * 1.5
            tp_pips = current_atr * 3.0
            
            if signal == "buy":
                sl = current_price - sl_pips
                tp = current_price + tp_pips
            else:
                sl = current_price + sl_pips
                tp = current_price - tp_pips
                
            return {
                "signal": signal,
                "type": trade_type,
                "sl": sl,
                "tp": tp,
                "price": current_price
            }

        return None
