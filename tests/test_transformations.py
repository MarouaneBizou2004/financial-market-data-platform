"""
Automated Unit Tests: Transformations & Feature Engineering
"""

import pytest
import pandas as pd
import numpy as np
from src.transformations.spark_transform import SparkMarketTransformer

@pytest.fixture
def synthetic_silver_df():
    """Generates continuous synthetic price series for 300 trading days."""
    dates = pd.date_range(start="2023-01-01", periods=300, freq="B").strftime("%Y-%m-%d")
    np.random.seed(42)
    
    records = []
    # Asset 1: Trending up
    p1 = 100.0
    for d in dates:
        ret = np.random.normal(0.001, 0.015)
        p1 *= (1 + ret)
        records.append({
            "symbol": "ASSET_A",
            "date": d,
            "open": p1 * 0.99,
            "high": p1 * 1.02,
            "low": p1 * 0.98,
            "close": p1,
            "adjusted_close": p1,
            "volume": int(np.random.uniform(1e6, 5e6))
        })
        
    # Asset 2: Mean reverting
    p2 = 50.0
    for d in dates:
        ret = np.random.normal(0.000, 0.02)
        p2 *= (1 + ret)
        records.append({
            "symbol": "ASSET_B",
            "date": d,
            "open": p2 * 0.99,
            "high": p2 * 1.01,
            "low": p2 * 0.98,
            "close": p2,
            "adjusted_close": p2,
            "volume": int(np.random.uniform(5e5, 2e6))
        })
        
    return pd.DataFrame(records)

def test_spark_transformer_vectorized_execution(synthetic_silver_df):
    """Verify that transformation produces correct feature columns and calculations."""
    transformer = SparkMarketTransformer()
    gold_df = transformer.transform_vectorized(synthetic_silver_df)
    
    # Required feature columns
    required_cols = [
        "daily_return", "return_5d", "return_20d", "return_60d",
        "volatility_20d", "volatility_60d",
        "sma_20", "sma_50", "sma_200",
        "sma_20_ratio", "sma_50_ratio", "sma_200_ratio",
        "avg_volume_20d", "volume_ratio",
        "rolling_max_close", "drawdown",
        "momentum_1m", "momentum_3m", "momentum_6m", "momentum_12m"
    ]
    for col in required_cols:
        assert col in gold_df.columns, f"Expected column {col} missing from Gold Layer"
        
    assert len(gold_df) == len(synthetic_silver_df)

def test_drawdown_bounds(synthetic_silver_df):
    """Verify that drawdowns are strictly non-positive (<= 0.0) and >= -1.0."""
    transformer = SparkMarketTransformer()
    gold_df = transformer.transform_vectorized(synthetic_silver_df)
    
    clean_dd = gold_df["drawdown"].dropna()
    assert (clean_dd <= 0.00001).all(), "Drawdown cannot be positive"
    assert (clean_dd >= -1.0).all(), "Drawdown cannot be less than -100%"

def test_moving_average_ratios(synthetic_silver_df):
    """Verify that SMA ratios equal close / SMA."""
    transformer = SparkMarketTransformer()
    gold_df = transformer.transform_vectorized(synthetic_silver_df)
    
    valid_sma = gold_df.dropna(subset=["sma_20", "sma_20_ratio", "close"])
    expected_ratio = valid_sma["close"] / valid_sma["sma_20"]
    diff = np.abs(valid_sma["sma_20_ratio"] - expected_ratio)
    assert (diff < 1e-4).all(), "SMA 20 ratio does not match close / sma_20"
