# System Architecture Documentation
## Financial Market Data Platform

### 1. Executive Architecture Overview
The **Financial Market Data Platform** is an enterprise-grade quantitative data platform built using modern data engineering and analytics patterns. It implements the **Medallion Data Architecture** (Bronze $\rightarrow$ Silver $\rightarrow$ Gold), a Kimball Star Schema analytical warehouse, an automated dbt transformation layer, Apache Airflow workflow orchestration, and a Machine Learning Market Regime detection engine with strict zero-leakage temporal constraints.

```
                      +-----------------------------+
                      |   Yahoo Finance Public API  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Python Ingestion Engine  |
                      |   (yfinance, batch UUID)    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |         Bronze Layer        |
                      |   (Raw + Ingestion Audit)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Data Quality Validator   |
                      |  (Checks, Cleansing, Rules) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |         Silver Layer        |
                      |     (Cleansed Daily OHLCV)  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  PySpark Window Transformer |
                      | (Returns, Vol, SMA, DD, Mom)|
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |          Gold Layer         |
                      |   (Analytical Feature Store)|
                      +-------+--------------+------+
                              |              |
              +---------------+              +----------------+
              |                                               |
              v                                               v
+---------------------------+                   +---------------------------+
|    Kimball Star Schema    |                   |    ML Market Regime Engine|
| (PostgreSQL / SQLite DWH) |                   |  (HistGradientBoosting)   |
+-------------+-------------+                   +-------------+-------------+
              |                                               |
              v                                               |
+---------------------------+                                 |
|   dbt Transformation Hub  |                                 |
|  (Staging -> Int -> Marts)|                                 |
+-------------+-------------+                                 |
              |                                               |
              +-----------------------+-----------------------+
                                      |
                                      v
                      +-------------------------------+
                      | Streamlit Interactive Portal  |
                      | (Analytics, Scorecards, Risk) |
                      +-------------------------------+
```

---

### 2. Medallion Layer Specifications

#### 2.1 Bronze Layer (`data/bronze/`)
- **Nature:** Append-only raw data partition with immutable audit metadata.
- **Enrichment:** Every row is stamped with `ingestion_timestamp` (ISO UTC), `source` (`Yahoo Finance (yfinance API)`), and `batch_id` (UUIDv4).
- **Format:** Partitioned Apache Parquet (`bronze_market_data.parquet`) and dual-format CSV for universal interoperability.

#### 2.2 Silver Layer (`data/silver/`)
- **Nature:** Cleansed, deduplicated, and structurally reconciled market data.
- **Validation Pipeline:**
  1. Deduplication on composite natural key `(symbol, date)`.
  2. Complete non-positive price filtering (`open > 0, high > 0, low > 0, close > 0`).
  3. Negative volume clipping ($\ge 0$).
  4. OHLC envelope reconciliation:
     $$High \ge \max(Open, Close) - \epsilon$$
     $$Low \le \min(Open, Close) + \epsilon$$
     $$High \ge Low$$
  5. Single-day abnormal price anomaly detection ($> +150\%$ or $< -85\%$).
- **Audit:** Automatically publishes `reports/data_quality_report.md` detailing execution metrics and pass rate (100.0%).

#### 2.3 Gold Layer (`data/gold/`)
- **Nature:** Highly enriched, analytical feature store containing rolling window metrics and technical indicators.
- **Engine:** PySpark Window Functions (`Window.partitionBy("symbol").orderBy("date")`) with high-performance vectorized fallback.
- **Metrics Computed:**
  - Arithmetic and Log Returns across 1D, 5D, 20D, and 60D horizons.
  - Annualized rolling volatilities (20D, 60D) scaled by $\sqrt{252}$.
  - Simple Moving Averages (20D, 50D, 200D) and Price-to-SMA ratios.
  - 20-day Volume Moving Averages and Volume Spikes ($Volume > 2.0 \times SMA_{20}^{vol}$).
  - Continuous Peak-to-Trough Drawdowns bounded in $[-1.0, 0.0]$.
  - Multi-horizon cross-sectional momentum (1M, 3M, 6M, 12M).

---

### 3. Data Warehouse & Kimball Modeling
The platform implements an analytical Star Schema optimized for high-throughput OLAP queries:
- **`dim_asset`:** Slowly Changing Dimension containing asset metadata (`symbol`, `asset_name`, `asset_type`, `sector`, `industry`, `exchange`, `currency`).
- **`dim_date`:** Date Dimension with integer smart surrogate key (`date_key = YYYYMMDD`), calendar quarter, month, day of week, and trading day flags.
- **`fact_market_daily`:** Fact table at grain **one row per asset per trading day**, with foreign keys referencing both dimensions. Foreign keys and composite indexes are enforced.

---

### 4. dbt Transformation Models
The platform organizes SQL transformations into modular, testable dbt layers:
- **Staging (`models/staging/`):** `stg_assets`, `stg_market_prices` with strict casting, renaming, and basic deduplication.
- **Intermediate (`models/intermediate/`):** `int_daily_returns`, `int_rolling_metrics`, `int_risk_metrics` computing windowed return aggregates.
- **Marts (`models/marts/`):**
  - `mart_asset_performance`: Lifetime CAGR, total return, volatility, Sharpe ratio, and price extremes.
  - `mart_risk_dashboard`: 1-year trailing risk profile, maximum drawdown, and abnormal volume days.
  - `mart_monthly_performance`: Calendar year and month return matrices.
- **Data Tests:** Built-in schema tests (`unique`, `not_null`) and custom singular SQL tests (`assert_positive_prices`, `assert_valid_drawdown_bounds`).

---

### 5. Machine Learning Regime Architecture
- **Target Regimes:** 4 distinct economic regimes defined by volatility and momentum.
- **Zero-Leakage Guarantee:** Forward-chaining walk-forward temporal splits (Train $\le 2023$, Val $= 2024$, Test $= 2025$). Rolling median volatility uses strictly trailing 252-day windows.
- **Champion Model:** `HistGradientBoostingClassifier` achieved 88.76% accuracy and 0.6744 Macro F1 on the 2025 out-of-sample holdout test set.

---

### 6. Workflow Orchestration
- **Apache Airflow DAG (`airflow/dags/market_data_pipeline.py`):** 7 sequential idempotent tasks with automatic retries and SLA monitoring.
- **Local Master Runner (`main.py`):** Single-command orchestration for rapid local execution and benchmarking.
