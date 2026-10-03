"""
Correlation & Co-movement Analytics Module
Computes cross-asset Pearson and Spearman correlation matrices and rolling pairwise correlations.
"""

from typing import Optional
import pandas as pd

def compute_correlation_matrix(
    returns_df: pd.DataFrame,
    method: str = "pearson"
) -> pd.DataFrame:
    """
    Computes pairwise correlation matrix of daily asset returns.
    method: 'pearson' (linear) or 'spearman' (rank order).
    """
    return returns_df.corr(method=method).round(4)

def compute_rolling_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int = 60
) -> pd.Series:
    """Computes rolling correlation between two asset return streams."""
    aligned = pd.concat([series_a, series_b], axis=1).dropna()
    col_a, col_b = aligned.columns[0], aligned.columns[1]
    return aligned[col_a].rolling(window=window, min_periods=window // 2).corr(aligned[col_b])
