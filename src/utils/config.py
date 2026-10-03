"""
Centralized Configuration Module
Loads paths, assets.yml, environment variables, database connections,
and financial market constants.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
import yaml
from dotenv import load_dotenv

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
BRONZE_DATA_DIR = DATA_DIR / "bronze"
SILVER_DATA_DIR = DATA_DIR / "silver"
GOLD_DATA_DIR = DATA_DIR / "gold"
SQL_DIR = PROJECT_ROOT / "sql"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
MODELS_DIR = PROJECT_ROOT / "models"
DASHBOARDS_DIR = PROJECT_ROOT / "dashboards"
DOCS_DIR = PROJECT_ROOT / "docs"

# Ensure runtime directories exist
for directory in [RAW_DATA_DIR, BRONZE_DATA_DIR, SILVER_DATA_DIR, GOLD_DATA_DIR, REPORTS_DIR, FIGURES_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Load .env file
load_dotenv(PROJECT_ROOT / ".env")

# Asset Universe Configuration File
ASSETS_CONFIG_PATH = CONFIG_DIR / "assets.yml"

def load_assets_config(config_path: Path = ASSETS_CONFIG_PATH) -> Dict[str, Any]:
    """Loads and validates the assets.yml configuration file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Assets config file not found at: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Financial & Market Constants
TRADING_DAYS_PER_YEAR = 252
ANNUAL_RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", "0.035")) # 3.5%
DEFAULT_START_DATE = os.getenv("START_DATE", "2021-01-01")
DEFAULT_END_DATE = os.getenv("END_DATE", "2025-12-31")

# Machine Learning Walk-Forward Split Dates (Strict Temporal Splitting)
ML_TRAIN_END = "2023-12-31"
ML_VAL_END = "2024-12-31"
ML_TEST_END = "2025-12-31"

# Database Connection Settings
# Supports PostgreSQL in Docker, with automatic fallback to DuckDB / SQLite for local zero-dependency testing
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "market_warehouse")

POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
SQLITE_DB_PATH = DATA_DIR / "market_warehouse.db"
DUCKDB_PATH = DATA_DIR / "market_warehouse.duckdb"
