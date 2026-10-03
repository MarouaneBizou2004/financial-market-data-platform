"""
Momentum Analytics Module
Computes multi-horizon momentum scores (1M, 3M, 6M, 12M) and cross-sectional universe rankings.
"""

from typing import List, Dict
import pandas as pd
import numpy as np

def compute_asset_momentum(
    prices: pd.Series,
    lookback_days: int = 126
) -> float:
    """Computes percentage price change over lookback window: (P_t - P_{t-k}) / P_{t-k}."""
    clean = prices.dropna()
    if len(clean) <= lookback_days:
        return 0.0
    p_now = clean.iloc[-1]
    p_past = clean.iloc[-lookback_days - 1]
    return float((p_now - p_past) / p_past)

def compute_universe_momentum_rankings(
    prices_pivot: pd.DataFrame,
    horizons: Dict[str, int] = None
) -> pd.DataFrame:
    """
    Computes multi-period momentum scores across the full asset universe:
    - 1 Month (21 trading days)
    - 3 Months (63 trading days)
    - 6 Months (126 trading days)
    - 12 Months (252 trading days)
    """
    if horizons is None:
        horizons = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}
        
    rankings = []
    for symbol in prices_pivot.columns:
        p_series = prices_pivot[symbol].dropna()
        row = {"symbol": symbol}
        for h_name, h_days in horizons.items():
            if len(p_series) > h_days:
                p_now = p_series.iloc[-1]
                p_past = p_series.iloc[-h_days - 1]
                row[f"momentum_{h_name}"] = round(float((p_now - p_past) / p_past) * 100.0, 2)
            else:
                row[f"momentum_{h_name}"] = np.nan
        rankings.append(row)
        
    df_rankings = pd.DataFrame(rankings)
    if "momentum_6M" in df_rankings.columns:
        df_rankings = df_rankings.sort_values(by="momentum_6M", ascending=False).reset_index(drop=True)
    return df_rankings
