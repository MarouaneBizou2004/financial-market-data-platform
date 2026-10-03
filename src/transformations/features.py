"""
Modular Feature Engineering Library
Provides standalone, pure functions for computing financial time-series features.
These functions are directly unit-tested and reused across pipelines, notebooks, and models.
"""

from typing import Union
import pandas as pd
import numpy as np

def calculate_returns(series: pd.Series, periods: int = 1) -> pd.Series:
    """Calculates simple arithmetic percentage return over specified period."""
    return series.pct_change(periods=periods)

def calculate_log_returns(series: pd.Series) -> pd.Series:
    """Calculates continuously compounded logarithmic return: ln(P_t / P_{t-1})."""
    return np.log(series / series.shift(1))

def calculate_rolling_volatility(
    returns: pd.Series,
    window: int = 20,
    annualize: bool = True,
    trading_days: int = 252
) -> pd.Series:
    """Calculates rolling standard deviation of returns, annualized by sqrt(trading_days)."""
    factor = np.sqrt(trading_days) if annualize else 1.0
    return returns.rolling(window=window, min_periods=max(5, window // 2)).std() * factor

def calculate_moving_average(series: pd.Series, window: int = 20) -> pd.Series:
    """Calculates rolling simple moving average."""
    return series.rolling(window=window, min_periods=max(5, window // 2)).mean()

def calculate_drawdown(series: pd.Series) -> pd.Series:
    """
    Calculates percentage drawdown from running historical peak:
    DD_t = (P_t - max_{tau <= t} P_tau) / max_{tau <= t} P_tau
    """
    running_max = series.cummax()
    return (series - running_max) / running_max

def calculate_volume_ratio(volume_series: pd.Series, window: int = 20) -> pd.Series:
    """Calculates ratio of current volume to historical rolling average volume."""
    avg_vol = volume_series.rolling(window=window, min_periods=max(5, window // 2)).mean()
    return np.where(avg_vol > 0, volume_series / avg_vol, 1.0)
