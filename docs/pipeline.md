# Pipeline Operations & Orchestration Guide
## Financial Market Data Platform

### 1. End-to-End Pipeline Workflow
The pipeline orchestrates the progression of market quotes from public endpoints to business dashboards and ML services across seven sequential phases:

```
[Phase 1: Ingestion]
        │
        ▼
[Phase 2: Validation] ──(Generates Quality Audit Report)
        │
        ▼
[Phase 3: Transformation] ──(Computes Gold Feature Layer)
        │
        ▼
[Phase 4: Warehouse ETL] ──(Populates Kimball Star Schema)
        │
        ▼
[Phase 5: dbt Pipeline] ──(Executes Staging/Marts + Tests)
        │
        ▼
[Phase 6: Machine Learning] ──(Trains & Deploys Regime Classifier)
        │
        ▼
[Phase 7: Dashboard & Analytics] ──(Streamlit & Analytical Reports)
```

---

### 2. Execution Methods

#### 2.1 Single-Command Master Runner (CLI)
To execute the complete pipeline locally:
```bash
python main.py
```
This runs the full ingestion, validation, feature engineering, relational loading, dbt execution, ML training, and report generation in sequence with structured logging and timing benchmarks.

#### 2.2 Orchestration via Apache Airflow
The platform includes a production DAG configured in `airflow/dags/market_data_pipeline.py`:
- **Schedule Interval:** Daily at `00:00 UTC` on market days (`0 0 * * 1-5`).
- **Catchup:** `False` (avoids duplicate runs).
- **Retries:** 2 retries with a 5-minute exponential backoff.
- **Tasks:**
  1. `extract_market_data`
  2. `validate_raw_data`
  3. `transform_with_spark`
  4. `load_postgres`
  5. `run_dbt_models`
  6. `run_data_quality_checks`
  7. `generate_reports`

To start the Airflow environment via Docker:
```bash
docker-compose up -d airflow-webserver airflow-scheduler
```
Access the Airflow UI at `http://localhost:8080` (credentials: `airflow` / `airflow`).

---

### 3. Idempotency & Data Freshness Guarantees

1. **Deterministic Slicing:** Each daily run overwrites or appends partitioned data keyed by `(symbol, date)` ensuring re-running the pipeline never duplicates facts.
2. **Atomic Batch UUIDs:** Ingestion batches are stamped with an immutable UUIDv4, ensuring traceability in audit logs.
3. **Foreign Key Integrity:** Database loads verify foreign keys against `dim_asset` and `dim_date` prior to fact insertions.
4. **Zero Lookahead Leakage:** ML feature pipelines compute rolling median volatilities on trailing 252-day windows, preventing future market conditions from leaking into model training.

---

### 4. Failure Modes & Operational Recovery

| Failure Scenario | Automated Safeguard | Manual Recovery Action |
| :--- | :--- | :--- |
| **API Rate Limiting / Timeout** | Exponential backoff retry (up to 3 attempts). Fallback to latest raw Parquet snapshot. | Verify network connectivity or inspect `data/raw/raw_market_data_latest.parquet`. |
| **Missing OHLC Data in Quotes** | Cleansing engine drops null rows and logs missing count in `reports/data_quality_report.md`. | Review provider feed for symbol delisting or ticker change. |
| **Corrupted High/Low Envelopes** | Cleansing engine reconciles envelopes: $H = \max(H, O, C)$, $L = \min(L, O, C)$. | Logged in validation metrics for audit. |
| **dbt Test Assertion Failure** | Pipeline halts immediately if negative prices or positive drawdowns occur. | Inspect SQLite/PostgreSQL warehouse tables and review `dbt/tests/`. |
| **JVM Missing on Local Host** | Spark transformer automatically activates high-performance Vectorized Engine. | Fully transparent fallback; no manual intervention required. |

---

### 5. Verification & Testing Commands

To run the complete automated test suite:
```bash
python -m pytest tests/ -v
```

To run individual pipeline stages:
```bash
# Ingestion only
python -m src.ingestion.market_data

# Validation & Silver Cleansing
python -m src.validation.market_checks

# PySpark Feature Engineering
python -m src.transformations.spark_transform

# Warehouse Relational Loader
python -m src.utils.database

# dbt Models & Quality Tests
python src/transformations/dbt_runner.py

# Machine Learning Training
python -m src.ml.train

# Launch Streamlit Dashboard
streamlit run dashboards/app.py
```
