"""
Automated Unit Tests: Machine Learning & Zero-Leakage Validation
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.utils.config import GOLD_DATA_DIR, MODELS_DIR
from src.ml.feature_pipeline import MarketRegimeFeaturePipeline, REGIME_LABELS
from src.ml.predict import MarketRegimePredictor

@pytest.fixture
def synthetic_gold_data():
    """Generates 1000 days of synthetic Gold Layer data for SPY."""
    dates = pd.date_range("2021-01-01", periods=1000, freq="B").strftime("%Y-%m-%d")
    np.random.seed(42)
    
    records = []
    price = 380.0
    for d in dates:
        ret = np.random.normal(0.0005, 0.012)
        price *= (1.0 + ret)
        records.append({
            "symbol": "SPY",
            "date": d,
            "open": price * 0.995,
            "high": price * 1.008,
            "low": price * 0.992,
            "close": price,
            "adjusted_close": price,
            "volume": 75000000,
            "daily_return": ret,
            "return_5d": ret * 5,
            "return_20d": ret * 20,
            "return_60d": ret * 60,
            "volatility_20d": 0.15,
            "volatility_60d": 0.16,
            "sma_20": price * 0.99,
            "sma_50": price * 0.98,
            "sma_200": price * 0.95,
            "sma_20_ratio": 1.01,
            "sma_50_ratio": 1.02,
            "sma_200_ratio": 1.05,
            "volume_ratio": 1.0,
            "drawdown": -0.04,
            "momentum_1m": 0.02,
            "momentum_3m": 0.05,
            "momentum_6m": 0.10,
            "momentum_12m": 0.18
        })
    return pd.DataFrame(records)

def test_feature_pipeline_regimes(synthetic_gold_data):
    """Verify that regime targets are created with valid classes {0, 1, 2, 3}."""
    pipeline = MarketRegimeFeaturePipeline(benchmark_symbol="SPY")
    df_ml = pipeline.build_features_and_regimes(synthetic_gold_data)
    
    assert "regime_target" in df_ml.columns
    assert "regime_name" in df_ml.columns
    unique_regimes = set(df_ml["regime_target"].unique())
    assert unique_regimes.issubset({0, 1, 2, 3})
    for r in unique_regimes:
        assert r in REGIME_LABELS

def test_strict_zero_leakage_temporal_split():
    """
    CRITICAL: Validates that data splits preserve strict chronological order
    with zero future data leakage. Train < Val < Test.
    """
    pipeline = MarketRegimeFeaturePipeline(benchmark_symbol="SPY")
    dates = pd.date_range("2021-01-01", "2025-12-31", freq="B").strftime("%Y-%m-%d")
    df_dummy = pd.DataFrame({
        "date": dates,
        "daily_return": 0.001,
        "return_5d": 0.005,
        "return_20d": 0.02,
        "return_60d": 0.05,
        "volatility_20d": 0.15,
        "volatility_60d": 0.15,
        "sma_20_ratio": 1.0,
        "sma_50_ratio": 1.0,
        "sma_200_ratio": 1.0,
        "volume_ratio": 1.0,
        "drawdown": -0.02,
        "momentum_3m": 0.03,
        "momentum_6m": 0.06,
        "regime_target": 0
    })
    
    train_df, val_df, test_df = pipeline.split_temporal(
        df_dummy,
        train_end="2023-12-31",
        val_end="2024-12-31",
        test_end="2025-12-31"
    )
    
    # 1. Non-empty splits
    assert len(train_df) > 0, "Train split should not be empty"
    assert len(val_df) > 0, "Validation split should not be empty"
    assert len(test_df) > 0, "Test split should not be empty"
    
    # 2. Strict chronological ordering (Zero lookahead leakage)
    max_train_date = pd.to_datetime(train_df["date"]).max()
    min_val_date = pd.to_datetime(val_df["date"]).min()
    max_val_date = pd.to_datetime(val_df["date"]).max()
    min_test_date = pd.to_datetime(test_df["date"]).min()
    
    assert max_train_date < min_val_date, f"Train max date ({max_train_date}) must precede Val min date ({min_val_date})"
    assert max_val_date < min_test_date, f"Val max date ({max_val_date}) must precede Test min date ({min_test_date})"

def test_trained_model_inference():
    """Verify saved champion model loads and produces valid prediction probabilities."""
    model_file = MODELS_DIR / "market_regime_model.joblib"
    gold_file = GOLD_DATA_DIR / "gold_market_features.parquet"
    
    if not model_file.exists() or not gold_file.exists():
        pytest.skip("Model artifact or Gold dataset not yet generated.")
        
    predictor = MarketRegimePredictor(model_path=model_file)
    df_gold = pd.read_parquet(gold_file)
    prediction = predictor.predict_latest_regime(df_gold)
    
    assert "predicted_regime_id" in prediction
    assert prediction["predicted_regime_id"] in [0, 1, 2, 3]
    assert "regime_probabilities" in prediction
    
    # Check that probabilities sum to 1.0
    total_prob = sum(prediction["regime_probabilities"].values())
    assert abs(total_prob - 1.0) < 1e-3, f"Probabilities must sum to 1.0, got {total_prob}"
