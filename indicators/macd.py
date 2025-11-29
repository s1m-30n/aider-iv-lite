import talib
import numpy as np
from typing import Tuple

def calculate_macd(close_prices: np.ndarray, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Moving Average Convergence Divergence (MACD).

    Args:
        close_prices (np.ndarray): Array of close prices.
        fastperiod (int): The short period. Default is 12.
        slowperiod (int): The long period. Default is 26.
        signalperiod (int): The signal line period. Default is 9.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: MACD line, Signal line, MACD Histogram.
    """
    if len(close_prices) < slowperiod:
        return np.array([]), np.array([]), np.array([])

    # Ensure input is float type for talib
    close_prices = close_prices.astype(float)

    macd, macdsignal, macdhist = talib.MACD(close_prices, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
    return macd, macdsignal, macdhist
