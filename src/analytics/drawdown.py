"""
Drawdown & Downside Risk Analytics Module
Computes historical drawdowns, maximum drawdown (MDD), peak-trough coordinates,
and drawdown duration in trading days.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

def compute_drawdown_series(prices: pd.Series) -> pd.Series:
    """Computes percentage drop from cumulative historical peak."""
    running_max = prices.cummax()
    return (prices - running_max) / running_max

def analyze_maximum_drawdown(prices: pd.Series) -> Dict[str, Any]:
    """
    Computes Maximum Drawdown (MDD) and locates the peak, trough, and recovery dates:
    - max_drawdown: Minimum percentage value (e.g. -0.245 for -24.5%)
    - peak_date: Date preceding the decline
    - trough_date: Date where bottom was reached
    - recovery_date: Date where previous peak was re-attained (or None if unrecovered)
    - duration_days: Number of trading days in drawdown state
    """
    clean_p = prices.dropna()
    if clean_p.empty:
        return {
            "max_drawdown": 0.0,
            "peak_date": None,
            "trough_date": None,
            "recovery_date": None,
            "drawdown_duration": 0
        }
        
    running_max = clean_p.cummax()
    dd_series = (clean_p - running_max) / running_max
    
    trough_idx = dd_series.idxmin()
    max_dd = float(dd_series.loc[trough_idx])
    
    # Peak date is the date of highest price on or before trough
    peak_slice = clean_p.loc[:trough_idx]
    peak_idx = peak_slice.idxmax()
    peak_val = clean_p.loc[peak_idx]
    
    # Recovery date: first date after trough where price >= peak_val
    post_trough = clean_p.loc[trough_idx:]
    recovered = post_trough[post_trough >= peak_val]
    recovery_idx = recovered.index[0] if not recovered.empty else None
    
    # Calculate duration
    if recovery_idx is not None:
        duration = len(clean_p.loc[peak_idx:recovery_idx])
    else:
        duration = len(clean_p.loc[peak_idx:])
        
    return {
        "max_drawdown": round(max_dd, 4),
        "peak_date": str(peak_idx),
        "trough_date": str(trough_idx),
        "recovery_date": str(recovery_idx) if recovery_idx else "Unrecovered",
        "drawdown_duration_days": int(duration)
    }
