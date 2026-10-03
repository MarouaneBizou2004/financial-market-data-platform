"""
Returns Analytics Module
Computes daily, weekly, monthly, cumulative, and Compound Annual Growth Rate (CAGR).
"""

from typing import Union
import pandas as pd
import numpy as np

def calculate_daily_returns(prices: pd.Series) -> pd.Series:
    """Calculates single-day percentage return: (P_t - P_{t-1}) / P_{t-1}."""
    return prices.pct_change(fill_method=None)

def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """Calculates compounded cumulative return: prod(1 + R_t) - 1."""
    return (1.0 + returns.fillna(0.0)).cumprod() - 1.0

def calculate_cagr(prices: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calculates Compound Annual Growth Rate (CAGR):
    CAGR = (P_end / P_start) ** (periods_per_year / N) - 1
    """
    clean = prices.dropna()
    if len(clean) < 2:
        return 0.0
    start_price = float(clean.iloc[0])
    end_price = float(clean.iloc[-1])
    n_periods = len(clean)
    if start_price <= 0 or n_periods <= 1:
        return 0.0
    return float((end_price / start_price) ** (periods_per_year / n_periods) - 1.0)

def calculate_periodic_returns(prices_df: pd.DataFrame, freq: str = "ME") -> pd.DataFrame:
    """
    Resamples daily price series to weekly, monthly, or annual frequency and computes returns.
    freq: 'W' for weekly, 'ME' for month-end, 'YE' for year-end.
    """
    resampled = prices_df.resample(freq).last()
    return resampled.pct_change(fill_method=None).dropna(how="all")
