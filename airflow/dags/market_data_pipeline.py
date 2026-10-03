"""
Airflow Production Market Data Pipeline DAG
Orchestrates end-to-end extraction, validation, Spark transformation, warehouse loading,
dbt execution, data quality verification, and analytical reporting.
"""

from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.bash import BashOperator
    from airflow.utils.dates import days_ago
except ImportError:
    # Standalone mock fallback for local execution without Airflow daemon
    DAG = None
    PythonOperator = None
    BashOperator = None

default_args = {
    "owner": "data-engineering-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
    "execution_timeout": timedelta(minutes=30)
}

def extract_market_data(**kwargs):
    """Task 1: Ingests raw public market data from Yahoo Finance API."""
    from src.ingestion.market_data import MarketDataIngestor
    ingestor = MarketDataIngestor()
    df_bronze = ingestor.run()
    return f"Extracted {len(df_bronze):,} raw bronze records."

def validate_raw_data(**kwargs):
    """Task 2: Executes integrity checks (duplicates, nulls, OHLC bounds) -> Silver."""
    from src.validation.market_checks import MarketDataValidator
    validator = MarketDataValidator()
    df_silver = validator.run()
    return f"Validated {len(df_silver):,} clean silver records."

def transform_with_spark(**kwargs):
    """Task 3: Applies distributed Window transformations -> Gold analytical features."""
    from src.transformations.spark_transform import SparkMarketTransformer
    transformer = SparkMarketTransformer()
    df_gold = transformer.run()
    return f"Generated {len(df_gold):,} gold feature records."

def load_warehouse(**kwargs):
    """Task 4: Loads Star Schema dimensions and facts into PostgreSQL / Analytical DB."""
    from src.utils.database import MarketWarehouseManager
    manager = MarketWarehouseManager()
    manager.execute_etl()
    return "Warehouse Star Schema loaded."

def run_dbt_models(**kwargs):
    """Task 5: Builds staging views, intermediate models, and gold mart tables."""
    from src.transformations.dbt_runner import DBTModelRunner
    runner = DBTModelRunner()
    runner.run_all()
    return "dbt models and assertions executed."

def run_data_quality_checks(**kwargs):
    """Task 6: Executes automated test suite asserting zero data drift or corruption."""
    from src.validation.market_checks import MarketDataValidator
    validator = MarketDataValidator()
    report_path = validator.generate_data_quality_report()
    return f"Quality audit completed. Report at {report_path}"

def generate_reports(**kwargs):
    """Task 7: Generates ML market regime inference and updates executive artifacts."""
    from src.ml.train import MarketRegimeTrainer
    trainer = MarketRegimeTrainer()
    metrics = trainer.run_training_pipeline()
    return f"Trained champion model: {metrics['model_metadata']['champion_architecture']}"

if DAG is not None:
    with DAG(
        dag_id="market_data_pipeline",
        default_args=default_args,
        description="End-to-end financial market data pipeline from Yahoo Finance to Gold Marts & ML",
        schedule_interval="0 22 * * 1-5", # Runs at 22:00 UTC on market trading days (Mon-Fri)
        start_date=datetime(2024, 1, 1),
        catchup=False,
        max_active_runs=1,
        tags=["financial-markets", "medallion", "spark", "dbt", "ml"]
    ) as dag:

        t1_extract = PythonOperator(
            task_id="extract_market_data",
            python_callable=extract_market_data,
        )

        t2_validate = PythonOperator(
            task_id="validate_raw_data",
            python_callable=validate_raw_data,
        )

        t3_transform = PythonOperator(
            task_id="transform_with_spark",
            python_callable=transform_with_spark,
        )

        t4_load = PythonOperator(
            task_id="load_postgres",
            python_callable=load_warehouse,
        )

        t5_dbt = PythonOperator(
            task_id="run_dbt_models",
            python_callable=run_dbt_models,
        )

        t6_quality = PythonOperator(
            task_id="run_data_quality_checks",
            python_callable=run_data_quality_checks,
        )

        t7_reports = PythonOperator(
            task_id="generate_reports",
            python_callable=generate_reports,
        )

        # DAG Dependency Pipeline
        t1_extract >> t2_validate >> t3_transform >> t4_load >> t5_dbt >> t6_quality >> t7_reports
