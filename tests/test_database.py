"""
Automated Unit Tests: Warehouse Database & Star Schema Queries
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path
from src.utils.database import MarketWarehouseManager
from src.utils.config import SQL_DIR

@pytest.fixture
def temp_db(tmp_path):
    """Initializes a temporary SQLite database with complete Star Schema."""
    test_db_path = tmp_path / "test_warehouse.db"
    mgr = MarketWarehouseManager(db_path=test_db_path)
    mgr.initialize_schema()
    return mgr

def test_schema_tables_exist(temp_db):
    """Verify that dim_asset, dim_date, and fact_market_daily tables are created."""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        
    assert "dim_asset" in tables
    assert "dim_date" in tables
    assert "fact_market_daily" in tables

def test_load_dim_asset(temp_db):
    """Verify that dim_asset loads configured instruments."""
    asset_map = temp_db.load_dim_asset()
    assert len(asset_map) >= 15
    assert "AAPL" in asset_map
    assert "SPY" in asset_map

def test_referential_integrity(temp_db):
    """Verify foreign key constraint enforcement in SQLite."""
    temp_db.load_dim_asset()
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        # Attempt to insert fact record with non-existent asset_key (e.g. 999999)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO fact_market_daily (
                    market_date_key, asset_key, open, high, low, close, adjusted_close, volume
                ) VALUES (20240102, 999999, 100.0, 105.0, 99.0, 104.0, 104.0, 1000000);
            """)

def test_analytical_query_execution():
    """Verify that SQL analytical query executes successfully against populated warehouse."""
    from src.utils.config import SQLITE_DB_PATH
    if not SQLITE_DB_PATH.exists():
        pytest.skip("Production SQLite database not found. Skipping live query execution.")
        
    mgr = MarketWarehouseManager(db_path=SQLITE_DB_PATH)
    perf_query = (SQL_DIR / "analytics" / "01_asset_performance.sql").read_text(encoding="utf-8")
    
    with mgr.get_connection() as conn:
        df_result = pd.read_sql_query(perf_query, conn)
        
    assert len(df_result) > 0
    assert "symbol" in df_result.columns
    assert "annualized_return_pct" in df_result.columns
    assert "annualized_volatility_pct" in df_result.columns
    assert "sharpe_ratio" in df_result.columns
