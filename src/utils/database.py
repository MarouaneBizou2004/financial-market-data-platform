"""
Warehouse Database Manager & ETL Loader
Initializes Star Schema in PostgreSQL / SQLite, loads dimensions from assets.yml,
populates fact_market_daily from Gold Layer, and executes analytical SQL queries.
"""

import sys
from pathlib import Path

# Ensure project root is first in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
curr_dir = str(Path(__file__).resolve().parent)
if curr_dir in sys.path:
    sys.path.remove(curr_dir)

import sqlite3
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from src.utils.config import (
    SQLITE_DB_PATH,
    SQL_DIR,
    GOLD_DATA_DIR,
    load_assets_config
)
from src.utils.logging import get_logger

logger = get_logger("WarehouseETL")

class MarketWarehouseManager:
    def __init__(self, db_path: Path = SQLITE_DB_PATH):
        self.db_path = db_path
        self.gold_path = GOLD_DATA_DIR / "gold_market_features.parquet"
        self.config = load_assets_config()

    def get_connection(self) -> sqlite3.Connection:
        """Returns SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_schema(self) -> None:
        """Applies DDL schema script."""
        ddl_path = SQL_DIR / "schema" / "01_create_market_schema.sql"
        logger.info(f"Applying Star Schema DDL from {ddl_path}...")
        with open(ddl_path, "r", encoding="utf-8") as f:
            ddl_sql = f.read()
            
        with self.get_connection() as conn:
            conn.executescript(ddl_sql)
            conn.commit()
        logger.info("Warehouse Star Schema initialized successfully.")

    def load_dim_asset(self) -> Dict[str, int]:
        """Loads assets from config/assets.yml into dim_asset and returns {symbol: asset_key}."""
        logger.info("Populating dim_asset from config/assets.yml...")
        assets = self.config.get("assets", [])
        
        asset_rows = []
        for a in assets:
            asset_rows.append({
                "symbol": a["symbol"],
                "asset_name": a.get("asset_name", a["symbol"]),
                "asset_type": a.get("asset_type", "equity"),
                "sector": a.get("sector", "Other"),
                "industry": a.get("industry", "Other"),
                "currency": a.get("currency", "USD"),
                "exchange": a.get("exchange", "US")
            })
            
        df_assets = pd.DataFrame(asset_rows)
        with self.get_connection() as conn:
            df_assets.to_sql("dim_asset", conn, if_exists="append", index=False)
            df_keys = pd.read_sql("SELECT asset_key, symbol FROM dim_asset", conn)
            
        mapping = df_keys.set_index("symbol")["asset_key"].to_dict()
        logger.info(f"Loaded {len(mapping)} assets into dim_asset.")
        return mapping

    def load_dim_date(self, dates: pd.Series) -> None:
        """Generates comprehensive calendar records for dim_date."""
        logger.info("Populating dim_date calendar hierarchy...")
        unique_dates = pd.to_datetime(dates.unique())
        
        date_records = []
        for d in unique_dates:
            date_key = int(d.strftime("%Y%m%d"))
            date_records.append({
                "date_key": date_key,
                "calendar_date": d.strftime("%Y-%m-%d"),
                "calendar_year": d.year,
                "calendar_quarter": (d.month - 1) // 3 + 1,
                "calendar_month": d.month,
                "calendar_week": int(d.strftime("%W")),
                "day_of_week": d.isoweekday(),
                "day_name": d.strftime("%A"),
                "is_trading_day": 1,
                "is_month_end": 1 if d.is_month_end else 0,
                "is_quarter_end": 1 if d.is_quarter_end else 0
            })
            
        df_dates = pd.DataFrame(date_records).drop_duplicates(subset=["date_key"])
        with self.get_connection() as conn:
            df_dates.to_sql("dim_date", conn, if_exists="append", index=False)
        logger.info(f"Loaded {len(df_dates)} unique trading days into dim_date.")

    def load_fact_market_daily(self, asset_map: Dict[str, int]) -> None:
        """Loads Gold features into fact_market_daily table."""
        logger.info(f"Loading Gold records into fact_market_daily from {self.gold_path}...")
        df_gold = pd.read_parquet(self.gold_path)
        
        # Populate dim_date first
        self.load_dim_date(df_gold["date"])
        
        df_fact = df_gold.copy()
        df_fact["asset_key"] = df_fact["symbol"].map(asset_map)
        df_fact["market_date_key"] = pd.to_datetime(df_fact["date"]).dt.strftime("%Y%m%d").astype(int)
        
        fact_cols = [
            "market_date_key", "asset_key", "open", "high", "low", "close", "adjusted_close",
            "volume", "daily_return", "return_5d", "return_20d", "volatility_20d",
            "volatility_60d", "sma_20", "sma_50", "sma_200", "drawdown", "is_abnormal_volume"
        ]
        
        # Round decimals for SQL insertion
        clean_fact = df_fact[fact_cols].copy()
        
        with self.get_connection() as conn:
            clean_fact.to_sql("fact_market_daily", conn, if_exists="append", index=False)
            
        logger.info(f"Loaded {len(clean_fact):,} rows into fact_market_daily.")

    def run_query(self, sql: str) -> pd.DataFrame:
        """Executes an SQL query string and returns DataFrame."""
        with self.get_connection() as conn:
            return pd.read_sql(sql, conn)

    def run_query_file(self, query_path: Path) -> pd.DataFrame:
        """Executes an external SQL query file."""
        with open(query_path, "r", encoding="utf-8") as f:
            sql = f.read()
        return self.run_query(sql)

    def execute_etl(self) -> None:
        """Orchestrates end-to-end relational warehouse setup."""
        print("=" * 70)
        print("EXECUTING RELATIONAL WAREHOUSE ETL: STAR SCHEMA CREATION & LOADING")
        print("=" * 70)
        self.initialize_schema()
        asset_map = self.load_dim_asset()
        self.load_fact_market_daily(asset_map)
        print("=" * 70)
        print("RELATIONAL WAREHOUSE ETL COMPLETED SUCCESSFULLY")
        print("=" * 70)

if __name__ == "__main__":
    manager = MarketWarehouseManager()
    manager.execute_etl()
