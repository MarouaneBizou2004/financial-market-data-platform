"""
Master Pipeline Orchestrator & CLI Runner
Executes the full end-to-end data pipeline:
1. Ingestion: Fetches authentic market data -> Bronze Layer
2. Validation: Data quality checks -> Silver Layer & Quality Report
3. Transformation: PySpark Window functions -> Gold Feature Store
4. Warehouse ETL: Kimball Star Schema population (dim_asset, dim_date, fact_market_daily)
5. dbt Runner: Executes staging, intermediate, marts, and schema test assertions
6. Machine Learning: Zero-leakage temporal split, model benchmarking, artifact persistence
"""

import sys
import time
import argparse
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging import get_logger
from src.ingestion.market_data import MarketDataIngestor
from src.validation.market_checks import MarketDataValidator
from src.transformations.spark_transform import SparkMarketTransformer
from src.utils.database import MarketWarehouseManager
from src.transformations.dbt_runner import run_dbt_pipeline
from src.ml.train import MarketRegimeTrainer

logger = get_logger("MasterOrchestrator")

def run_pipeline(skip_ingestion: bool = False):
    total_start = time.time()
    timings = {}
    
    print("\n" + "=" * 80)
    print("FINANCIAL MARKET DATA PLATFORM: END-TO-END PIPELINE EXECUTION")
    print("=" * 80 + "\n")
    
    # ---------------------------------------------------------
    # Phase 1: Ingestion
    # ---------------------------------------------------------
    if not skip_ingestion:
        print("[1/6] Running Data Ingestion Engine...")
        t0 = time.time()
        ingestor = MarketDataIngestor()
        df_bronze = ingestor.run()
        timings["1. Ingestion (Bronze Layer)"] = round(time.time() - t0, 2)
    else:
        print("[1/6] Skipping Ingestion (Using existing Bronze layer)...")
        timings["1. Ingestion (Bronze Layer)"] = 0.0

    # ---------------------------------------------------------
    # Phase 2: Validation
    # ---------------------------------------------------------
    print("\n[2/6] Running Data Quality Validation Engine...")
    t0 = time.time()
    validator = MarketDataValidator()
    df_silver = validator.run()
    timings["2. Validation (Silver Layer)"] = round(time.time() - t0, 2)

    # ---------------------------------------------------------
    # Phase 3: Spark Transformations
    # ---------------------------------------------------------
    print("\n[3/6] Running PySpark / Distributed Feature Engineering...")
    t0 = time.time()
    transformer = SparkMarketTransformer()
    df_gold = transformer.run()
    timings["3. Feature Engineering (Gold Layer)"] = round(time.time() - t0, 2)

    # ---------------------------------------------------------
    # Phase 4: Warehouse Star Schema ETL
    # ---------------------------------------------------------
    print("\n[4/6] Populating Kimball Star Schema Warehouse...")
    t0 = time.time()
    warehouse_mgr = MarketWarehouseManager()
    warehouse_mgr.execute_etl()
    timings["4. Warehouse Star Schema ETL"] = round(time.time() - t0, 2)

    # ---------------------------------------------------------
    # Phase 5: dbt Transformations & Data Tests
    # ---------------------------------------------------------
    print("\n[5/6] Executing dbt Transformation Models & Integrity Tests...")
    t0 = time.time()
    run_dbt_pipeline()
    timings["5. dbt Models & Tests"] = round(time.time() - t0, 2)

    # ---------------------------------------------------------
    # Phase 6: Machine Learning Training & Inference
    # ---------------------------------------------------------
    print("\n[6/6] Training & Benchmarking Market Regime ML Models...")
    t0 = time.time()
    trainer = MarketRegimeTrainer()
    trainer.run_training_pipeline()
    timings["6. ML Training & Walk-Forward Eval"] = round(time.time() - t0, 2)

    total_time = round(time.time() - total_start, 2)

    # ---------------------------------------------------------
    # Execution Summary & Performance Metrics
    # ---------------------------------------------------------
    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION SUMMARY & BENCHMARKS")
    print("=" * 80)
    for phase, elapsed in timings.items():
        print(f"  {phase:<38}: {elapsed:>6.2f}s")
    print("-" * 80)
    print(f"  {'Total Elapsed Execution Time':<38}: {total_time:>6.2f}s")
    print("=" * 80)
    print("\nAll pipeline components, warehouse tables, dbt marts, and ML models are ready.")
    print("Launch interactive dashboard using: streamlit run dashboards/app.py\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Financial Market Data Platform Master Runner")
    parser.add_argument("--skip-ingestion", action="store_true", help="Skip public API fetch and use local Bronze parquet")
    args = parser.parse_args()
    
    run_pipeline(skip_ingestion=args.skip_ingestion)
