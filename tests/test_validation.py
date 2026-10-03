"""
Automated Unit Tests: Data Validation & Quality Checks
"""

import pytest
import pandas as pd
import numpy as np
from src.validation.market_checks import MarketDataValidator

@pytest.fixture
def sample_bronze_df():
    """Generates synthetic Bronze DataFrame for testing edge cases."""
    return pd.DataFrame({
        "symbol": ["AAPL", "AAPL", "AAPL", "MSFT", "MSFT"],
        "date": ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-02", "2024-01-03"],
        "open": [185.0, 185.0, 186.0, 370.0, 375.0],
        "high": [187.0, 187.0, 188.0, 374.0, 378.0],
        "low": [184.0, 184.0, 185.0, 368.0, 372.0],
        "close": [186.5, 186.5, 187.5, 372.5, 377.0],
        "adjusted_close": [186.0, 186.0, 187.0, 372.0, 376.5],
        "volume": [50000000, 50000000, 48000000, 25000000, 26000000],
        "ingestion_timestamp": ["2024-01-04 00:00:00 UTC"] * 5,
        "source": ["Test Source"] * 5,
        "batch_id": ["test-batch-uuid"] * 5
    })

def test_duplicate_removal(sample_bronze_df):
    """Verify that duplicated records for (symbol, date) are detected and removed."""
    validator = MarketDataValidator()
    silver_df, metrics = validator.validate_and_clean(sample_bronze_df)
    
    assert metrics["duplicate_records_removed"] == 1
    assert len(silver_df) == 4
    # Ensure no duplicates remain
    assert silver_df.duplicated(subset=["symbol", "date"]).sum() == 0

def test_non_positive_price_filtering():
    """Verify that rows with non-positive prices are eliminated."""
    df_invalid = pd.DataFrame({
        "symbol": ["AAPL", "AAPL", "AAPL"],
        "date": ["2024-01-02", "2024-01-03", "2024-01-04"],
        "open": [180.0, -10.0, 182.0],  # negative open
        "high": [185.0, 185.0, 0.0],     # zero high
        "low": [179.0, 175.0, 180.0],
        "close": [183.0, 182.0, 181.0],
        "adjusted_close": [183.0, 182.0, 181.0],
        "volume": [1000, 1000, 1000]
    })
    validator = MarketDataValidator()
    silver_df, metrics = validator.validate_and_clean(df_invalid)
    assert metrics["non_positive_price_records"] == 2
    assert len(silver_df) == 1

def test_negative_volume_clipping():
    """Verify that negative volumes are clipped to zero without crashing."""
    df_neg_vol = pd.DataFrame({
        "symbol": ["AAPL"],
        "date": ["2024-01-02"],
        "open": [180.0],
        "high": [185.0],
        "low": [179.0],
        "close": [183.0],
        "adjusted_close": [183.0],
        "volume": [-5000]
    })
    validator = MarketDataValidator()
    silver_df, metrics = validator.validate_and_clean(df_neg_vol)
    assert metrics["negative_volume_records"] == 1
    assert silver_df.iloc[0]["volume"] == 0

def test_ohlc_reconciliation():
    """Verify that High < Open/Close or Low > Open/Close is reconciled to preserve valid envelopes."""
    df_bad_ohlc = pd.DataFrame({
        "symbol": ["TEST"],
        "date": ["2024-01-02"],
        "open": [100.0],
        "high": [95.0],    # High is less than open (invalid!)
        "low": [105.0],    # Low is greater than open (invalid!)
        "close": [102.0],
        "adjusted_close": [102.0],
        "volume": [1000]
    })
    validator = MarketDataValidator()
    silver_df, metrics = validator.validate_and_clean(df_bad_ohlc)
    assert metrics["invalid_ohlc_relationships_reconciled"] == 1
    row = silver_df.iloc[0]
    assert row["high"] >= max(row["open"], row["close"])
    assert row["low"] <= min(row["open"], row["close"])
