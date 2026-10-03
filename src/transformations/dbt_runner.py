"""
dbt Model Executor & Validation Runner
Compiles and executes dbt staging, intermediate, and marts models against the analytical warehouse,
and runs automated dbt singular and schema assertion tests.
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
import sqlite3
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
curr_dir = str(Path(__file__).resolve().parent)
if curr_dir in sys.path:
    sys.path.remove(curr_dir)

from src.utils.config import SQLITE_DB_PATH
from src.utils.logging import get_logger

logger = get_logger("DBTRunner")

class DBTModelRunner:
    def __init__(self, db_path: Path = SQLITE_DB_PATH):
        self.db_path = db_path
        self.dbt_dir = PROJECT_ROOT / "dbt"
        self.models_dir = self.dbt_dir / "models"
        self.tests_dir = self.dbt_dir / "tests"

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def compile_model_sql(self, sql_content: str) -> str:
        """Resolves {{ ref('model') }} and {{ source(...) }} jinja syntax into SQL table names."""
        # Replace {{ ref('...') }} with table name
        resolved = re.sub(r"\{\{\s*ref\('([^']+)'\)\s*\}\}", r"\1", sql_content)
        # Replace {{ source('...', '...') }} with table name
        resolved = re.sub(r"\{\{\s*source\('[^']+',\s*'([^']+)'\)\s*\}\}", r"\1", resolved)
        return resolved

    def run_staging_models(self) -> None:
        """Materializes staging models as SQL views."""
        logger.info("Building dbt Staging Models (views)...")
        staging_dir = self.models_dir / "staging"
        
        with self.get_connection() as conn:
            for sql_file in sorted(staging_dir.glob("*.sql")):
                model_name = sql_file.stem
                with open(sql_file, "r", encoding="utf-8") as f:
                    raw_sql = f.read()
                compiled_sql = self.compile_model_sql(raw_sql)
                
                drop_sql = f"DROP VIEW IF EXISTS {model_name};"
                create_sql = f"CREATE VIEW {model_name} AS {compiled_sql}"
                
                conn.execute(drop_sql)
                conn.execute(create_sql)
                logger.info(f"  [OK] Created view: {model_name}")
            conn.commit()

    def run_intermediate_models(self) -> None:
        """Materializes intermediate models as SQL views."""
        logger.info("Building dbt Intermediate Models (views)...")
        int_dir = self.models_dir / "intermediate"
        
        with self.get_connection() as conn:
            for sql_file in sorted(int_dir.glob("*.sql")):
                model_name = sql_file.stem
                with open(sql_file, "r", encoding="utf-8") as f:
                    raw_sql = f.read()
                compiled_sql = self.compile_model_sql(raw_sql)
                
                drop_sql = f"DROP VIEW IF EXISTS {model_name};"
                create_sql = f"CREATE VIEW {model_name} AS {compiled_sql}"
                
                conn.execute(drop_sql)
                conn.execute(create_sql)
                logger.info(f"  [OK] Created view: {model_name}")
            conn.commit()

    def run_mart_models(self) -> None:
        """Materializes marts models as physical reporting tables."""
        logger.info("Building dbt Mart Models (tables)...")
        marts_dir = self.models_dir / "marts"
        
        with self.get_connection() as conn:
            for sql_file in sorted(marts_dir.glob("*.sql")):
                model_name = sql_file.stem
                with open(sql_file, "r", encoding="utf-8") as f:
                    raw_sql = f.read()
                compiled_sql = self.compile_model_sql(raw_sql)
                
                # Materialize as table
                drop_sql = f"DROP TABLE IF EXISTS {model_name};"
                create_sql = f"CREATE TABLE {model_name} AS {compiled_sql}"
                
                conn.execute(drop_sql)
                conn.execute(create_sql)
                
                count = conn.execute(f"SELECT COUNT(*) FROM {model_name}").fetchone()[0]
                logger.info(f"  [OK] Materialized table: {model_name} ({count:,} rows)")
            conn.commit()

    def run_dbt_tests(self) -> Dict[str, str]:
        """Runs singular and schema assertion tests."""
        logger.info("Running dbt validation test suite...")
        test_results = {}
        
        with self.get_connection() as conn:
            # 1. Singular tests
            for test_file in sorted(self.tests_dir.glob("*.sql")):
                test_name = test_file.stem
                with open(test_file, "r", encoding="utf-8") as f:
                    raw_sql = f.read()
                compiled_sql = self.compile_model_sql(raw_sql)
                
                violations = pd.read_sql(compiled_sql, conn)
                if len(violations) == 0:
                    test_results[test_name] = "PASSED"
                    logger.info(f"  [PASSED] Singular test: {test_name}")
                else:
                    test_results[test_name] = f"FAILED ({len(violations)} violations)"
                    logger.error(f"  [FAILED] Singular test {test_name}: {len(violations)} failures")
                    
            # 2. Generic schema assertions (Unique, Not Null on marts)
            marts_tests = [
                ("mart_asset_performance", "symbol", "unique"),
                ("mart_asset_performance", "annualized_volatility_pct", "not_null"),
                ("mart_risk_dashboard", "symbol", "unique"),
                ("mart_risk_dashboard", "max_drawdown_pct", "not_null")
            ]
            for table, col, ttype in marts_tests:
                t_name = f"{table}_{col}_{ttype}"
                if ttype == "unique":
                    q = f"SELECT {col}, COUNT(*) FROM {table} GROUP BY {col} HAVING COUNT(*) > 1;"
                else:
                    q = f"SELECT * FROM {table} WHERE {col} IS NULL;"
                res = pd.read_sql(q, conn)
                if len(res) == 0:
                    test_results[t_name] = "PASSED"
                    logger.info(f"  [PASSED] Schema test: {t_name}")
                else:
                    test_results[t_name] = f"FAILED ({len(res)} violations)"
                    logger.error(f"  [FAILED] Schema test {t_name}")
                    
        return test_results

    def run_all(self) -> None:
        print("=" * 70)
        print("EXECUTING DBT TRANSFORMATIONS & INTEGRITY TEST SUITE")
        print("=" * 70)
        self.run_staging_models()
        self.run_intermediate_models()
        self.run_mart_models()
        test_res = self.run_dbt_tests()
        print("=" * 70)
        print("DBT MODELS & TESTS COMPLETED SUCCESSFULLY")
        for t, status in test_res.items():
            print(f" - {t:40s}: {status}")
        print("=" * 70)

def run_dbt_pipeline(db_path: Path = SQLITE_DB_PATH) -> None:
    """Convenience function to execute all dbt models and schema tests."""
    runner = DBTModelRunner(db_path=db_path)
    runner.run_all()

if __name__ == "__main__":
    run_dbt_pipeline()
