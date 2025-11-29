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

    def analyze_symbol(self, symbol: str, data: dict) -> dict:
        """
        Analyze a symbol for trade opportunities using cascading top-down analysis.
        
        Args:
            symbol (str): The symbol to analyze.
            data (dict): Dictionary of DataFrames for different timeframes.
                         Keys: 'D1', 'H4', 'H1', 'M15', 'M5'
            
        Returns:
            dict: Signal dictionary or None.
        """
        print(f"Analyzing {symbol}...")
        
        # Boom = Sell Only, Crash = Buy Only
        is_boom = "Boom" in symbol
        is_crash = "Crash" in symbol
        
        # 1. Analyze Higher Timeframe Bias (D1, H4, H1)
        d1_trend = self.analyze_trend(data.get('D1'))
        h4_trend = self.analyze_trend(data.get('H4'))
        h1_trend = self.analyze_trend(data.get('H1'))
        
        print(f"  Trends: D1={d1_trend}, H4={h4_trend}, H1={h1_trend}")
        
        bias = "neutral"
        if is_boom:
            # We want Sell.
            # 1. D1 is Bearish (Trend aligned) -> Good.
            # 2. D1 is Bullish BUT H4 and H1 are Bearish (Reversal/Pullback) -> Acceptable.
            if d1_trend == "bearish":
                if h4_trend == "bearish" or h1_trend == "bearish":
                     bias = "sell"
            elif d1_trend == "bullish":
                if h4_trend == "bearish" and h1_trend == "bearish":
                    bias = "sell"
                
        elif is_crash:
            # We want Buy.
            # 1. D1 is Bullish (Trend aligned) -> Good.
            # 2. D1 is Bearish BUT H4 and H1 are Bullish (Reversal/Pullback) -> Acceptable.
            if d1_trend == "bullish":
                if h4_trend == "bullish" or h1_trend == "bullish":
                    bias = "buy"
            elif d1_trend == "bearish":
                if h4_trend == "bullish" and h1_trend == "bullish":
                    bias = "buy"
        
        print(f"  Market Bias: {bias}")
        
        if bias == "neutral":
            return None
            
        # 2. If Bias is favorable, check for Entry on Lower Timeframes (M15, M5)
        # We can also check H1 for a Swing Entry if H1 is aligned.
        
        best_signal = None
        
        # Check M15/M5 for Scalp Entry
        # We pass the bias as the 'trend' argument to enforce direction
        scalp_signal = self.analyze_scalp(symbol, data.get('M15'), data.get('M5'), bias)
        print(scalp_signal)
        
        if scalp_signal:
            best_signal = scalp_signal
            print(f"  Found Scalp Setup: {scalp_signal['signal']}")
            
        return best_signal

    def analyze_trend(self, df: pd.DataFrame) -> str:
        """Determine trend from data using EMA 50."""
        if df is None or df.empty:
            return "neutral"
            
        close_prices = df['close'].values
        # Using EMA 50 for trend direction
        ema_50 = calculate_ema(close_prices, period=50)
        
        if len(ema_50) == 0:
            return "neutral"
            
        current_price = close_prices[-1]
        current_ema_50 = ema_50[-1]
        
        # Simple Trend: Price vs EMA
        if current_price > current_ema_50:
            return "bullish"
        else:
            return "bearish"



    def analyze_scalp(self, symbol: str, df_m15: pd.DataFrame, df_m5: pd.DataFrame, trend: str) -> dict:
        """Analyze for Scalp setups (M15/M5)."""
        if df_m15 is None or df_m15.empty or df_m5 is None or df_m5.empty:
            return None

        is_boom = "Boom" in symbol
        is_crash = "Crash" in symbol
        
        # Scalps can be counter-trend, but safer with trend.
        # Let's be strict: Boom (Sell), Crash (Buy).
        
        # M5 Entry
        close_prices = df_m5['close'].values
        upper_bb, _, lower_bb = calculate_bollinger_bands(close_prices)
        rsi = calculate_rsi(close_prices)
        atr = calculate_atr(df_m5['high'].values, df_m5['low'].values, close_prices)
        
        if len(rsi) == 0:
            return None
            
        current_price = close_prices[-1]
        current_rsi = rsi[-1]
        current_upper_bb = upper_bb[-1]
        current_lower_bb = lower_bb[-1]
        current_atr = atr[-1]
        
        signal = None
        
        if is_boom: # Sell
            # Price at Upper BB, RSI high
            print(f"    Scalp Check {symbol}: Price={current_price:.2f}, UpperBB={current_upper_bb:.2f}, RSI={current_rsi:.2f}")
            if current_price > current_upper_bb and current_rsi > 65:
                signal = "sell"
        elif is_crash: # Buy
            # Price at Lower BB, RSI low
            print(f"    Scalp Check {symbol}: Price={current_price:.2f}, LowerBB={current_lower_bb:.2f}, RSI={current_rsi:.2f}")
            if current_price < current_lower_bb and current_rsi < 35:
                signal = "buy"
                
        if signal:
            # Scalp targets are tighter
            sl_pips = current_atr * 1.5
            tp_pips = current_atr * 2.5 # Quick profit
            
            if signal == "buy":
                sl = current_price - sl_pips
                tp = current_price + tp_pips
            else:
                sl = current_price + sl_pips
                tp = current_price - tp_pips
                
            return {
                "signal": signal,
                "type": "scalp",
                "sl": sl,
                "tp": tp,
                "price": current_price
            }
            
        return None
