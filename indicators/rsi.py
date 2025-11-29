import talib
import numpy as np

def calculate_rsi(close_prices: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Relative Strength Index (RSI).

    Args:
        close_prices (np.ndarray): Array of close prices.
        period (int): The period for RSI calculation. Default is 14.

    Returns:
        np.ndarray: Array of RSI values.
    """
    if len(close_prices) < period:
        return np.array([])
    
    # Ensure input is float type for talib
    close_prices = close_prices.astype(float)
    
    return talib.RSI(close_prices, timeperiod=period)
