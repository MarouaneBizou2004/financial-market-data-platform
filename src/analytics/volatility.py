"""
Volatility Analytics Module
Computes rolling standard deviation, annualized volatility, and Parkinson high-low range volatility.
"""

import pandas as pd
import numpy as np

def calculate_annualized_volatility(
    returns: pd.Series,
    trading_days: int = 252
) -> float:
    """
    Computes sample annualized standard deviation of returns:
    sigma_{ann} = std(R) * sqrt(252)
    """
    clean_ret = returns.dropna()
    if len(clean_ret) < 2:
        return 0.0
    return float(clean_ret.std() * np.sqrt(trading_days))

def calculate_rolling_volatility_series(
    returns: pd.Series,
    window: int = 20,
    annualize: bool = True,
    trading_days: int = 252
) -> pd.Series:
    """Computes rolling historical volatility across sliding window."""
    factor = np.sqrt(trading_days) if annualize else 1.0
    return returns.rolling(window=window, min_periods=max(5, window // 2)).std() * factor

def calculate_parkinson_volatility(
    high: pd.Series,
    low: pd.Series,
    window: int = 20,
    trading_days: int = 252
) -> pd.Series:
    """
    Parkinson High-Low Extreme Value Volatility Estimator:
    sigma_p = sqrt( 252 / (4 * ln(2) * N) * sum( ln(H / L)^2 ) )
    Offers higher statistical efficiency than close-to-close volatility.
    """
    hl_ratio = np.log(high / low) ** 2
    factor = trading_days / (4.0 * np.log(2.0))
    rolling_sum = hl_ratio.rolling(window=window, min_periods=max(5, window // 2)).mean()
    return np.sqrt(rolling_sum * factor)
