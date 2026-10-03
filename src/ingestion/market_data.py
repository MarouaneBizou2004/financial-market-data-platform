"""
Market Data Ingestion Pipeline
Fetches authentic public daily OHLCV market data from Yahoo Finance via yfinance,
persists raw payloads, attaches ingestion audit metadata (batch_id, timestamp, source),
and creates the Bronze Data Layer.
"""

import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import yfinance as yf

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import (
    RAW_DATA_DIR,
    BRONZE_DATA_DIR,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    load_assets_config
)
from src.utils.logging import get_logger

logger = get_logger("IngestionPipeline")

class MarketDataIngestor:
    def __init__(
        self,
        start_date: str = DEFAULT_START_DATE,
        end_date: str = DEFAULT_END_DATE,
        config: Optional[Dict[str, Any]] = None
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.config = config or load_assets_config()
        self.assets = self.config.get("assets", [])
        self.symbols = [a["symbol"] for a in self.assets]
        self.batch_id = str(uuid.uuid4())
        
    def fetch_market_data(self) -> pd.DataFrame:
        """
        Fetches authentic daily OHLCV data for all configured symbols using yfinance.
        Handles multi-ticker responses and standardizes into a long-format raw DataFrame.
        """
        logger.info(f"Initiating market data fetch for {len(self.symbols)} symbols from {self.start_date} to {self.end_date}...")
        logger.info(f"Universe: {', '.join(self.symbols)}")
        
        try:
            # Download bulk data in one optimized request
            df_raw = yf.download(
                tickers=self.symbols,
                start=self.start_date,
                end=self.end_date,
                group_by="ticker",
                auto_adjust=False,
                threads=True,
                progress=False
            )
            
            records = []
            
            # Parse multi-ticker DataFrame structure
            if len(self.symbols) == 1:
                symbol = self.symbols[0]
                temp_df = df_raw.reset_index()
                for _, row in temp_df.iterrows():
                    records.append(self._extract_row_record(row, symbol))
            else:
                for symbol in self.symbols:
                    if symbol in df_raw.columns.levels[0]:
                        sym_df = df_raw[symbol].dropna(how="all").reset_index()
                        for _, row in sym_df.iterrows():
                            records.append(self._extract_row_record(row, symbol))
                            
            df_long = pd.DataFrame(records)
            logger.info(f"Successfully downloaded {len(df_long):,} raw market records across {len(self.symbols)} symbols.")
            return df_long
            
        except Exception as e:
            logger.error(f"Error fetching live market data: {e}")
            raise e

    def _extract_row_record(self, row: pd.Series, symbol: str) -> dict:
        """Standardizes a single OHLCV record from yfinance output."""
        date_val = pd.to_datetime(row["Date"]).strftime("%Y-%m-%d")
        
        open_val = float(row.get("Open", 0.0))
        high_val = float(row.get("High", 0.0))
        low_val = float(row.get("Low", 0.0))
        close_val = float(row.get("Close", 0.0))
        adj_close_val = float(row.get("Adj Close", close_val))
        vol_val = float(row.get("Volume", 0.0))
        
        return {
            "symbol": symbol,
            "date": date_val,
            "open": round(open_val, 4),
            "high": round(high_val, 4),
            "low": round(low_val, 4),
            "close": round(close_val, 4),
            "adjusted_close": round(adj_close_val, 4),
            "volume": int(vol_val)
        }

    def save_raw(self, df_raw: pd.DataFrame) -> Path:
        """Saves untouched raw payload to data/raw/."""
        raw_path = RAW_DATA_DIR / f"raw_market_data_{datetime.now().strftime('%Y%m%d')}.parquet"
        df_raw.to_parquet(raw_path, index=False)
        # Also maintain a latest pointer
        df_raw.to_parquet(RAW_DATA_DIR / "raw_market_data_latest.parquet", index=False)
        logger.info(f"Saved raw payload to: {raw_path}")
        return raw_path

    def create_bronze_layer(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Creates Bronze Layer by appending immutable lineage and audit metadata:
        ingestion_timestamp, source, batch_id.
        """
        logger.info("Enriching raw data into Medallion Bronze Layer with audit metadata...")
        df_bronze = df_raw.copy()
        
        from datetime import timezone
        df_bronze["ingestion_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        df_bronze["source"] = "Yahoo Finance (yfinance API)"
        df_bronze["batch_id"] = self.batch_id
        
        # Save to bronze
        bronze_path = BRONZE_DATA_DIR / "bronze_market_data.parquet"
        df_bronze.to_parquet(bronze_path, index=False)
        df_bronze.to_csv(BRONZE_DATA_DIR / "bronze_market_data.csv", index=False)
        
        logger.info(f"Bronze Layer successfully saved to: {bronze_path} ({len(df_bronze):,} rows)")
        return df_bronze

    def run(self) -> pd.DataFrame:
        """Executes full ingestion from public source to Bronze layer."""
        print("=" * 70)
        print("EXECUTING INGESTION PIPELINE: PUBLIC MARKET DATA -> BRONZE LAYER")
        print("=" * 70)
        df_raw = self.fetch_market_data()
        self.save_raw(df_raw)
        df_bronze = self.create_bronze_layer(df_raw)
        print("=" * 70)
        print("INGESTION & BRONZE LAYER GENERATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        return df_bronze

if __name__ == "__main__":
    ingestor = MarketDataIngestor()
    ingestor.run()
