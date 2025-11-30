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
        # print(f"Analyzing {symbol}...")
        
        # Boom = Sell Only, Crash = Buy Only
        is_boom = "Boom" in symbol
        is_crash = "Crash" in symbol
        
        # 1. Analyze Higher Timeframe Bias (D1, H4, H1)
        d1_trend = self.analyze_trend(data.get('D1'))
        h4_trend = self.analyze_trend(data.get('H4'))
        h1_trend = self.analyze_trend(data.get('H1'))
        
        # print(f"  Trends: D1={d1_trend}, H4={h4_trend}, H1={h1_trend}")
        
        bias = "neutral"
        if is_boom:
            # We want Sell.
            if d1_trend == "bearish":
                if h4_trend == "bearish" or h1_trend == "bearish":
                     bias = "sell"
            elif d1_trend == "bullish":
                if h4_trend == "bearish" and h1_trend == "bearish":
                    bias = "sell"
                
        elif is_crash:
            # We want Buy.
            if d1_trend == "bullish":
                if h4_trend == "bullish" or h1_trend == "bullish":
                    bias = "buy"
            elif d1_trend == "bearish":
                if h4_trend == "bullish" and h1_trend == "bullish":
                    bias = "buy"
        
        # print(f"  Market Bias: {bias}")
        
        # Spike Prediction (Informational)
        spike_pred = self.predict_spike(symbol, data.get('M5'))
        spike_prob = spike_pred['probability'] if spike_pred else 0.0
        
        # Prepare details for UI
        details = {
            "trend_d1": d1_trend,
            "trend_h4": h4_trend,
            "trend_h1": h1_trend,
            "bias": bias.upper(),
            "spike_prob": spike_prob,
            "price": data.get('M5')['close'].iloc[-1] if data.get('M5') is not None and not data.get('M5').empty else 0.0
        }
        
        if bias == "neutral":
            return None, details
            
        # 2. If Bias is favorable, check for Entry on Lower Timeframes (M15, M5)
        best_signal = None
        
        # Check M15/M5 for Scalp Entry
        scalp_signal = self.analyze_scalp(symbol, data.get('M15'), data.get('M5'), bias, spike_prob)
        
        if scalp_signal:
            best_signal = scalp_signal
            # print(f"  Found Scalp Setup: {scalp_signal['signal']}")
            
        return best_signal, details

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



    def analyze_scalp(self, symbol: str, df_m15: pd.DataFrame, df_m5: pd.DataFrame, trend: str, spike_prob: float = 0.0) -> dict:
        """Analyze for Scalp setups (M15/M5)."""
        if df_m15 is None or df_m15.empty or df_m5 is None or df_m5.empty:
            return None

        is_boom = "Boom" in symbol
        is_crash = "Crash" in symbol
        
        # M5 Entry
        close_prices = df_m5['close'].values
        upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(close_prices)
        rsi = calculate_rsi(close_prices)
        atr = calculate_atr(df_m5['high'].values, df_m5['low'].values, close_prices)
        
        if len(rsi) == 0:
            return None
            
        current_price = close_prices[-1]
        current_rsi = rsi[-1]
        current_upper_bb = upper_bb[-1]
        current_middle_bb = middle_bb[-1]
        current_lower_bb = lower_bb[-1]
        current_atr = atr[-1]
        
        # Safety Check: If spike is imminent (>60%), DO NOT TRADE
        if spike_prob > 60:
            # print(f"    ⚠️ High Spike Risk ({spike_prob}%), skipping scalp.")
            return None
            
        # Thresholds
        # If safe (low-ish spike risk), relax conditions significantly
        if spike_prob < 45:
            # Super Relaxed
            boom_rsi_thresh = 50
            crash_rsi_thresh = 50
            # Allow trading almost anywhere not extreme
            boom_price_cond = current_price > current_lower_bb # Just not hugging lower band
            crash_price_cond = current_price < current_upper_bb # Just not hugging upper band
        else:
            # Standard/Strict (when spike risk is moderate 45-60%)
            boom_rsi_thresh = 65
            crash_rsi_thresh = 35
            boom_price_cond = current_price > current_upper_bb
            crash_price_cond = current_price < current_lower_bb
        
        signal = None
        
        if is_boom: # Sell
            # print(f"    Scalp Check {symbol}: Price={current_price:.2f}, RSI={current_rsi:.2f} (Thresh: >{boom_rsi_thresh})")
            if boom_price_cond and current_rsi > boom_rsi_thresh:
                signal = "sell"
        elif is_crash: # Buy
            # print(f"    Scalp Check {symbol}: Price={current_price:.2f}, RSI={current_rsi:.2f} (Thresh: <{crash_rsi_thresh})")
            if crash_price_cond and current_rsi < crash_rsi_thresh:
                signal = "buy"
                
        if signal:
            # Scalp targets
            sl_dist = current_atr * 1.5
            tp_dist = current_atr * 3.0
            
            # Enforce minimums
            sl_dist = max(sl_dist, 10.0)
            tp_dist = max(tp_dist, 20.0)
            
            if signal == "buy":
                sl = current_price - sl_dist
                tp = current_price + tp_dist
            else:
                sl = current_price + sl_dist
                tp = current_price - tp_dist
                
            return {
                "signal": signal,
                "type": "scalp",
                "sl": sl,
                "tp": tp,
                "price": current_price
            }
            
        return None

    def predict_spike(self, symbol: str, df_m5: pd.DataFrame) -> dict:
        """
        Predict the likelihood of a spike based on statistics and technicals.
        
        Args:
            symbol (str): The symbol.
            df_m5 (pd.DataFrame): M5 Data.
            
        Returns:
            dict: Prediction details or None.
        """
        if df_m5 is None or df_m5.empty:
            return None
            
        is_boom = "Boom" in symbol
        is_crash = "Crash" in symbol
        
        # 1. Identify Past Spikes (Statistical)
        # Calculate body sizes
        opens = df_m5['open'].values
        closes = df_m5['close'].values
        
        bodies = np.abs(closes - opens)
        avg_body = np.mean(bodies)
        
        # Threshold for a "spike" (e.g., 3x average body)
        spike_threshold = avg_body * 3.0
        
        spikes_indices = []
        for i in range(len(closes)):
            body = bodies[i]
            is_bullish = closes[i] > opens[i]
            is_bearish = closes[i] < opens[i]
            
            if is_boom and is_bullish and body > spike_threshold:
                spikes_indices.append(i)
            elif is_crash and is_bearish and body > spike_threshold:
                spikes_indices.append(i)
                
        # Calculate average distance between spikes
        if len(spikes_indices) < 2:
            avg_distance = 0
            candles_since_last = 0
        else:
            distances = np.diff(spikes_indices)
            avg_distance = np.mean(distances)
            last_spike_idx = spikes_indices[-1]
            candles_since_last = len(closes) - 1 - last_spike_idx
            
        # 2. Technical Conditions
        rsi = calculate_rsi(closes)
        upper_bb, _, lower_bb = calculate_bollinger_bands(closes)
        slowk, slowd = calculate_stochastic(df_m5['high'].values, df_m5['low'].values, closes)
        
        if len(rsi) == 0 or len(slowk) == 0:
            return None
            
        current_rsi = rsi[-1]
        current_stoch_k = slowk[-1]
        current_price = closes[-1]
        
        probability = 0.0
        reasons = []
        
        # Statistical Factor
        if avg_distance > 0:
            ratio = candles_since_last / avg_distance
            if ratio > 0.8: # Approaching average time
                probability += 30
                reasons.append(f"Due for spike (Time: {candles_since_last}/{avg_distance:.1f})")
            if ratio > 1.5: # Overdue
                probability += 20
                reasons.append("Overdue")
                
        # Technical Factor
        if is_boom:
            if current_rsi < 30: # Oversold
                probability += 20
                reasons.append(f"RSI Oversold ({current_rsi:.1f})")
            if current_stoch_k < 20: # Stochastic Oversold
                probability += 20
                reasons.append(f"Stoch Oversold ({current_stoch_k:.1f})")
            if current_price < lower_bb[-1]: # Near Lower BB
                probability += 10
                reasons.append("Price below Lower BB")
        elif is_crash:
            if current_rsi > 70: # Overbought
                probability += 20
                reasons.append(f"RSI Overbought ({current_rsi:.1f})")
            if current_stoch_k > 80: # Stochastic Overbought
                probability += 20
                reasons.append(f"Stoch Overbought ({current_stoch_k:.1f})")
            if current_price > upper_bb[-1]: # Near Upper BB
                probability += 10
                reasons.append("Price above Upper BB")
                
        return {
            "probability": min(probability, 100),
            "reasons": reasons,
            "avg_distance": avg_distance,
            "candles_since_last": candles_since_last
        }
