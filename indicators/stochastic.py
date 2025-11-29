import talib
import numpy as np
from typing import Tuple

def calculate_stochastic(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, 
                         fastk_period: int = 5, slowk_period: int = 3, slowk_matype: int = 0, 
                         slowd_period: int = 3, slowd_matype: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Stochastic Oscillator.

    Args:
        high_prices (np.ndarray): Array of high prices.
        low_prices (np.ndarray): Array of low prices.
        close_prices (np.ndarray): Array of close prices.
        fastk_period (int): Time period for building the Fast-K line. Default is 5.
        slowk_period (int): Smoothing for making the Slow-K line. Default is 3.
        slowk_matype (int): Type of Moving Average for Slow-K. Default is 0 (SMA).
        slowd_period (int): Smoothing for making the Slow-D line. Default is 3.
        slowd_matype (int): Type of Moving Average for Slow-D. Default is 0 (SMA).

    Returns:
        Tuple[np.ndarray, np.ndarray]: Slow-K line, Slow-D line.
    """
    if len(close_prices) < fastk_period:
        return np.array([]), np.array([])

    # Ensure inputs are float type for talib
    high_prices = high_prices.astype(float)
    low_prices = low_prices.astype(float)
    close_prices = close_prices.astype(float)

    slowk, slowd = talib.STOCH(high_prices, low_prices, close_prices, 
                               fastk_period=fastk_period, 
                               slowk_period=slowk_period, slowk_matype=slowk_matype, 
                               slowd_period=slowd_period, slowd_matype=slowd_matype)
    return slowk, slowd
