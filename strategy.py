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
        spike_pred = self.predict_spike(symbol, data.get('M5'), data.get('M1'))
        spike_prob = spike_pred['probability'] if spike_pred else 0.0
        
        # Prepare details for UI
        details = {
            "trend_d1": d1_trend,
            "trend_h4": h4_trend,
            "trend_h1": h1_trend,
            "bias": bias.upper(),
            "spike_prob": spike_prob,
            "candles_since_spike": spike_pred.get('candles_since_spike') if spike_pred else None,
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

    def calculate_support_resistance(self, df: pd.DataFrame, lookback: int = 20) -> dict:
        """
        Identify short-term Support and Resistance levels.
        """
        if df is None or df.empty:
            return {'support': [], 'resistance': []}
            
        highs = df['high'].values
        lows = df['low'].values
        
        supports = []
        resistances = []
        
        # Simple local extrema
        for i in range(2, len(df) - 2):
            # Support: Low is lower than 2 previous and 2 next
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                supports.append(lows[i])
                
            # Resistance: High is higher than 2 previous and 2 next
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                resistances.append(highs[i])
                
        return {'support': supports[-3:], 'resistance': resistances[-3:]} # Return last 3

    def predict_spike(self, symbol: str, df_m5: pd.DataFrame, df_m1: pd.DataFrame = None) -> dict:
        """
        Predict the likelihood of a spike with high precision.
        Uses M5 for stats and M1 for immediate S/R and Technicals.
        """
        if df_m5 is None or df_m5.empty:
            return None
            
        is_boom = "Boom" in symbol
        is_crash = "Crash" in symbol
        
        # --- 1. Statistical (Time) Factor (Weight: 10%) ---
        # Use M5 for broader context of spike frequency
        opens = df_m5['open'].values
        closes = df_m5['close'].values
        bodies = np.abs(closes - opens)
        avg_body = np.mean(bodies)
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
                
        time_prob = 0.0
        reasons = []
        candles_since_last = None
        
        if len(spikes_indices) > 0:
            last_spike_idx = spikes_indices[-1]
            candles_since_last = len(closes) - 1 - last_spike_idx

        if len(spikes_indices) >= 2:
            distances = np.diff(spikes_indices)
            avg_distance = np.mean(distances)
            
            if avg_distance > 0:
                ratio = candles_since_last / avg_distance
                if ratio > 0.8: time_prob = 100
        
        # --- 2. Technical Factor (Weight: 30%) ---
        # Use M1 for precision if available, else M5
        df_tech = df_m1 if df_m1 is not None and not df_m1.empty else df_m5
        closes_tech = df_tech['close'].values
        
        rsi = calculate_rsi(closes_tech)
        slowk, slowd = calculate_stochastic(df_tech['high'].values, df_tech['low'].values, closes_tech)
        upper_bb, _, lower_bb = calculate_bollinger_bands(closes_tech)
        
        if len(rsi) == 0 or len(slowk) == 0:
            return None
            
        current_rsi = rsi[-1]
        current_stoch_k = slowk[-1]
        current_price = closes_tech[-1]
        
        tech_prob = 0.0
        
        if is_boom:
            if current_rsi < 30: tech_prob += 50
            if current_stoch_k < 20: tech_prob += 50
        elif is_crash:
            if current_rsi > 70: tech_prob += 50
            if current_stoch_k > 80: tech_prob += 50
            
        # --- 3. Support/Resistance Factor (Weight: 60%) ---
        # Critical for "Super Precision"
        sr_levels = self.calculate_support_resistance(df_tech)
        sr_prob = 0.0
        
        # Check proximity to levels (within 0.05% of price)
        threshold = current_price * 0.0005 
        
        if is_boom:
            # Look for Support
            for level in sr_levels['support']:
                if abs(current_price - level) < threshold:
                    sr_prob = 100
                    reasons.append(f"At Support ({level:.2f})")
                    break
            # Also check Lower BB as dynamic support
            if current_price <= lower_bb[-1]:
                sr_prob = max(sr_prob, 80)
                reasons.append("At Lower BB")
                
        elif is_crash:
            # Look for Resistance
            for level in sr_levels['resistance']:
                if abs(current_price - level) < threshold:
                    sr_prob = 100
                    reasons.append(f"At Resistance ({level:.2f})")
                    break
            # Also check Upper BB as dynamic resistance
            if current_price >= upper_bb[-1]:
                sr_prob = max(sr_prob, 80)
                reasons.append("At Upper BB")
                
        # --- Final Weighted Probability ---
        # Time: 10%, Technicals: 30%, S/R: 60%
        final_prob = (time_prob * 0.1) + (tech_prob * 0.3) + (sr_prob * 0.6)
        
        if final_prob > 50:
            reasons.append(f"Tech: {tech_prob}%")
            
        return {
            "probability": min(final_prob, 100),
            "reasons": reasons,
            "candles_since_spike": candles_since_last if len(spikes_indices) > 0 else None
        }

    def check_exit_conditions(self, symbol: str, df_m5: pd.DataFrame, position_type: int, open_time: float) -> tuple[bool, str]:
        """
        Check if any profit exit conditions are met.
        
        Strategies:
        1. N-Candle Scalp: Close after 5 candles.
        2. RSI Extremes: Close if RSI < 30 (Boom/Sell) or RSI > 70 (Crash/Buy).
        3. BB Mean Reversion: Close if price touches Middle Band.
        
        Args:
            symbol (str): Symbol name.
            df_m5 (pd.DataFrame): M5 Data.
            position_type (int): mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL.
            open_time (float): Timestamp of when the position was opened.
            
        Returns:
            tuple: (should_close, reason)
        """
        if df_m5 is None or df_m5.empty:
            return False, ""
            
        is_boom = "Boom" in symbol
        is_crash = "Crash" in symbol
        is_buy = position_type == mt5.ORDER_TYPE_BUY
        is_sell = position_type == mt5.ORDER_TYPE_SELL
        
        # Data
        closes = df_m5['close'].values
        times = df_m5['time'].values
        current_price = closes[-1]
        
        # --- 1. N-Candle Scalp (5 Candles) ---
        # Calculate how many M5 candles have passed since open_time
        # We can approximate this or count strictly from the dataframe
        
        # Find index of the candle that contains the open_time
        # Or simply: (current_time - open_time) / (5 * 60)
        
        current_time = times[-1].astype('datetime64[s]').astype(float) # Convert numpy datetime to timestamp float
        
        # If open_time is from MT5, it's a float timestamp.
        # Ensure we are comparing apples to apples.
        
        # Let's use simple time diff for robustness
        seconds_elapsed = current_time - open_time
        candles_elapsed = seconds_elapsed / 300 # 300 seconds in 5 mins
        
        if candles_elapsed >= 5:
            return True, f"N-Candle Scalp Target Reached ({int(candles_elapsed)} candles)"
            
        # --- 2. RSI Extremes ---
        rsi = calculate_rsi(closes)
        if len(rsi) > 0:
            current_rsi = rsi[-1]
            if is_boom and is_sell and current_rsi < 30:
                return True, f"RSI Oversold ({current_rsi:.1f}) - Reversal Risk"
            elif is_crash and is_buy and current_rsi > 70:
                return True, f"RSI Overbought ({current_rsi:.1f}) - Reversal Risk"
                
        # --- 3. BB Mean Reversion ---
        # upper, middle, lower = calculate_bollinger_bands(closes)
        # if len(middle) > 0:
        #     current_middle = middle[-1]
            
        #     # Check for touch/cross of middle band
        #     # For Sell (Boom): Price drops to Middle Band (Price <= Middle)
        #     # For Buy (Crash): Price rises to Middle Band (Price >= Middle)
            
        #     if is_boom and is_sell and current_price <= current_middle:
        #         return True, "Price touched Middle Bollinger Band"
        #     elif is_crash and is_buy and current_price >= current_middle:
        #         return True, "Price touched Middle Bollinger Band"
                
        return False, ""
