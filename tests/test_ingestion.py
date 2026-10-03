"""
Automated Unit Tests: Market Data Ingestion & Configuration
"""

import pytest
import pandas as pd
from pathlib import Path
from src.utils.config import load_assets_config, PROJECT_ROOT
from src.ingestion.market_data import MarketDataIngestor

def test_load_assets_config():
    """Verify that assets.yml loads correctly and contains all required structure."""
    config = load_assets_config()
    assert isinstance(config, dict), "Config must be a dictionary"
    assert "assets" in config, "Config must contain 'assets' key"
    assert "benchmark" in config, "Config must contain 'benchmark' key"
    assert "portfolio" in config, "Config must contain 'portfolio' key"

def test_asset_universe_integrity():
    """Verify asset universe validity, non-empty fields, and uniqueness."""
    config = load_assets_config()
    assets = config["assets"]
    assert len(assets) >= 15, "Universe should contain at least 15 assets"
    
    symbols = [a["symbol"] for a in assets]
    assert len(symbols) == len(set(symbols)), "All asset symbols must be unique"
    
    for a in assets:
        assert "symbol" in a and len(a["symbol"]) > 0
        assert "asset_name" in a and len(a["asset_name"]) > 0
        assert a["asset_type"] in ["equity", "etf"]
        assert "sector" in a and len(a["sector"]) > 0

def test_model_portfolio_weights_sum_to_one():
    """Verify that configured portfolio weights sum to 100%."""
    config = load_assets_config()
    weights = config["portfolio"]["weights"]
    total_weight = sum(weights.values())
    assert abs(total_weight - 1.0) < 1e-4, f"Portfolio weights must sum to 1.0, got {total_weight}"

def test_market_data_ingestor_initialization():
    """Verify that MarketDataIngestor initializes with correct universe and batch ID."""
    ingestor = MarketDataIngestor(start_date="2024-01-01", end_date="2024-01-31")
    assert len(ingestor.symbols) >= 15
    assert ingestor.batch_id is not None
    assert len(ingestor.batch_id) > 10

def test_extract_row_record_format():
    """Verify the standardization of single raw records."""
    ingestor = MarketDataIngestor()
    sample_row = pd.Series({
        "Date": pd.Timestamp("2024-01-15"),
        "Open": 150.25,
        "High": 152.00,
        "Low": 149.50,
        "Close": 151.75,
        "Adj Close": 151.00,
        "Volume": 45000000
    })
    record = ingestor._extract_row_record(sample_row, "TEST")
    assert record["symbol"] == "TEST"
    assert record["date"] == "2024-01-15"
    assert record["open"] == 150.25
    assert record["high"] == 152.00
    assert record["low"] == 149.50
    assert record["close"] == 151.75
    assert record["adjusted_close"] == 151.00
    assert record["volume"] == 45000000
