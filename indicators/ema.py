import talib
import numpy as np

def calculate_ema(close_prices: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Exponential Moving Average (EMA).

    Args:
        close_prices (np.ndarray): Array of close prices.
        period (int): The period for EMA calculation. Default is 14.

    Returns:
        np.ndarray: Array of EMA values.
    """
    if len(close_prices) < period:
        return np.array([])

    # Ensure input is float type for talib
    close_prices = close_prices.astype(float)

    return talib.EMA(close_prices, timeperiod=period)
