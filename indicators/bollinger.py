import talib
import numpy as np
from typing import Tuple

def calculate_bollinger_bands(close_prices: np.ndarray, period: int = 20, nbdevup: float = 2.0, nbdevdn: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Bollinger Bands.

    Args:
        close_prices (np.ndarray): Array of close prices.
        period (int): The period for moving average. Default is 20.
        nbdevup (float): Number of standard deviations for upper band. Default is 2.0.
        nbdevdn (float): Number of standard deviations for lower band. Default is 2.0.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: Upper band, Middle band, Lower band.
    """
    if len(close_prices) < period:
        return np.array([]), np.array([]), np.array([])

    # Ensure input is float type for talib
    close_prices = close_prices.astype(float)

    upper, middle, lower = talib.BBANDS(close_prices, timeperiod=period, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=0)
    return upper, middle, lower
