import talib
import numpy as np

def calculate_atr(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Average True Range (ATR).

    Args:
        high_prices (np.ndarray): Array of high prices.
        low_prices (np.ndarray): Array of low prices.
        close_prices (np.ndarray): Array of close prices.
        period (int): The period for ATR calculation. Default is 14.

    Returns:
        np.ndarray: Array of ATR values.
    """
    if len(close_prices) < period:
        return np.array([])

    # Ensure inputs are float type for talib
    high_prices = high_prices.astype(float)
    low_prices = low_prices.astype(float)
    close_prices = close_prices.astype(float)

    return talib.ATR(high_prices, low_prices, close_prices, timeperiod=period)
