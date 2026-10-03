"""
Machine Learning Feature Pipeline & Regime Target Construction
Extracts lagging time-series features and establishes economic market regimes
with strict guardrails preventing temporal and lookahead data leakage.
"""

from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np

from src.utils.config import (
    TRADING_DAYS_PER_YEAR,
    ML_TRAIN_END,
    ML_VAL_END,
    ML_TEST_END
)

REGIME_LABELS = {
    0: "Low Vol / Bull (Calm Expansion)",
    1: "Low Vol / Stagnant (Grinding Drift)",
    2: "High Vol / Bear (Crisis / Selloff)",
    3: "High Vol / Dynamic Rally (Volatile Rebound)"
}

class MarketRegimeFeaturePipeline:
    def __init__(self, benchmark_symbol: str = "SPY"):
        self.benchmark_symbol = benchmark_symbol
        self.feature_columns = [
            "daily_return", "return_5d", "return_20d", "return_60d",
            "volatility_20d", "volatility_60d",
            "sma_20_ratio", "sma_50_ratio", "sma_200_ratio",
            "volume_ratio", "drawdown",
            "momentum_3m", "momentum_6m"
        ]

    def build_features_and_regimes(self, df_gold: pd.DataFrame) -> pd.DataFrame:
        """
        Filters to benchmark asset (SPY) or composite universe to construct
        leakage-proof market regime targets and lagging predictors.
        """
        bench_df = df_gold[df_gold["symbol"] == self.benchmark_symbol].copy()
        bench_df = bench_df.sort_values(by="date").reset_index(drop=True)
        
        # Calculate trailing median volatility using a 1-year trailing window (prevents global future leakage)
        bench_df["trailing_median_vol"] = bench_df["volatility_60d"].rolling(252, min_periods=60).median()
        
        # If early history lacks 252d, backfill with trailing expanding median
        bench_df["trailing_median_vol"] = bench_df["trailing_median_vol"].fillna(bench_df["volatility_60d"].expanding(30).median())
        
        # Market Regime Rule Definition:
        # Regime 0: Low Volatility & Positive Momentum (Bull Expansion)
        # Regime 1: Low Volatility & Negative/Flat Momentum (Stagnant Drift)
        # Regime 2: High Volatility & Negative Momentum (Crisis / Bear Selloff)
        # Regime 3: High Volatility & Positive Momentum (Volatile Rebound / Rally)
        is_low_vol = bench_df["volatility_20d"] <= bench_df["trailing_median_vol"]
        is_positive_mom = bench_df["momentum_3m"] > 0.0
        
        regime_conditions = [
            (is_low_vol & is_positive_mom),
            (is_low_vol & ~is_positive_mom),
            (~is_low_vol & ~is_positive_mom),
            (~is_low_vol & is_positive_mom)
        ]
        regime_choices = [0, 1, 2, 3]
        
        bench_df["regime_target"] = np.select(regime_conditions, regime_choices, default=0)
        bench_df["regime_name"] = bench_df["regime_target"].map(REGIME_LABELS)
        
        # Drop warm-up rows where 200-day SMA or 60-day returns are NaN
        clean_df = bench_df.dropna(subset=self.feature_columns + ["regime_target"]).reset_index(drop=True)
        return clean_df

    def split_temporal(
        self,
        df: pd.DataFrame,
        train_end: str = ML_TRAIN_END,
        val_end: str = ML_VAL_END,
        test_end: str = ML_TEST_END
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Enforces strict chronological forward-chaining train/val/test splits.
        NEVER randomly shuffles time series records.
        """
        df["date"] = pd.to_datetime(df["date"])
        
        train_mask = (df["date"] <= pd.to_datetime(train_end))
        val_mask = (df["date"] > pd.to_datetime(train_end)) & (df["date"] <= pd.to_datetime(val_end))
        test_mask = (df["date"] > pd.to_datetime(val_end)) & (df["date"] <= pd.to_datetime(test_end))
        
        train_df = df[train_mask].copy().reset_index(drop=True)
        val_df = df[val_mask].copy().reset_index(drop=True)
        test_df = df[test_mask].copy().reset_index(drop=True)
        
        # Verify temporal boundaries (zero overlap)
        if not train_df.empty and not val_df.empty:
            assert train_df["date"].max() < val_df["date"].min(), "Temporal overlap between Train and Validation sets!"
        if not val_df.empty and not test_df.empty:
            assert val_df["date"].max() < test_df["date"].min(), "Temporal overlap between Validation and Test sets!"
            
        return train_df, val_df, test_df
