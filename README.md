# Financial Market Data Platform

[![CI Pipeline](https://github.com/MarouaneBizou2004/financial-market-data-platform/actions/workflows/tests.yml/badge.svg)](https://github.com/MarouaneBizou2004/financial-market-data-platform/actions)
[![Python 3.11 | 3.12 | 3.13](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Engine-PySpark%20%2F%20Vectorized-orange.svg)](https://spark.apache.org/)
[![dbt Core](https://img.shields.io/badge/Transformations-dbt%20Core-FF694B.svg)](https://www.getdbt.com/)
[![Apache Airflow](https://img.shields.io/badge/Orchestration-Apache%20Airflow-017CEE.svg)](https://airflow.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/Warehouse-PostgreSQL%20%2F%20SQLite-336791.svg)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, end-to-end quantitative financial market data platform designed for multi-asset market surveillance, financial time-series engineering, risk attribution, and machine learning market regime classification. Built on a Kimball Star Schema warehouse and Medallion architecture, the platform ingests authentic market feeds, transforms multi-horizon risk metrics using PySpark Window specifications, orchestrates workflows via Apache Airflow, executes analytical models via dbt Core, and serves an interactive quantitative portal in Streamlit.

---

## Architecture Diagram

```
                             +-----------------------------------+
                             |     Public Market Data Source     |
                             |   (Yahoo Finance Historical API)  |
                             +-----------------+-----------------+
                                               |
                                               v
                             +-----------------------------------+
                             |      Python Ingestion Engine      |
                             |    (Idempotent UUID Batching)     |
                             +-----------------+-----------------+
                                               |
                                               v
                             +-----------------------------------+
                             |        BRONZE DATA LAYER          |
                             |   (Raw Quotes + Audit Metadata)   |
                             +-----------------+-----------------+
                                               |
                                               v
                             +-----------------------------------+
                             |    Data Validation Engine         |
                             |   (OHLC Envelope, Bounds, Nulls)  |
                             +-----------------+-----------------+
                                               |
                                               v
                             +-----------------------------------+
                             |        SILVER DATA LAYER          |
                             |    (Cleansed Daily OHLCV Data)    |
                             +-----------------+-----------------+
                                               |
                                               v
                             +-----------------------------------+
                             |   PySpark Transformation Engine   |
                             |   (Window Specifications & Stats) |
                             +-----------------+-----------------+
                                               |
                                               v
                             +-----------------------------------+
                             |         GOLD DATA LAYER           |
                             |   (Analytical Feature Store 33-Col|
                             +--------+------------------+-------+
                                      |                  |
              +-----------------------+                  +-----------------------+
              |                                                                  |
              v                                                                  v
+-----------------------------+                                    +-----------------------------+
|    Analytical Data DWH      |                                    |   ML Market Regime Engine   |
|     Kimball Star Schema     |                                    |   HistGradientBoosting      |
|  (dim_asset, dim_date,      |                                    |  (Strict Zero-Leakage Split |
|   fact_market_daily)        |                                    |   Train<=23, Val=24, Test=25|
+--------------+--------------+                                    +--------------+--------------+
               |                                                                  |
               v                                                                  |
+-----------------------------+                                                   |
|    dbt Transformation Hub   |                                                   |
|  (Staging -> Int -> Marts)  |                                                   |
|  (Singular & Schema Tests)  |                                                   |
+--------------+--------------+                                                   |
               |                                                                  |
               +--------------------------------+---------------------------------+
                                                |
                                                v
                               +----------------------------------+
                               |   Streamlit Quantitative Portal  |
                               |  - Multi-Asset Performance       |
                               |  - Deep-Dive Technical Charts    |
                               |  - Downside Risk Scorecard       |
                               |  - Cross-Asset Correlation       |
                               |  - Market Regime Inference       |
                               |  - Euler Risk Attribution (CCR)  |
                               +----------------------------------+
```

---

## Technologies Used

| Domain | Technologies & Frameworks | Purpose in Project |
| :--- | :--- | :--- |
| **Core Language** | Python 3.11, 3.12, 3.13 | Primary object-oriented engineering, typing, algorithms |
| **Distributed Compute**| Apache Spark (PySpark), Vectorized Engine | Scalable sliding window feature transformations across assets |
| **Data Warehouse** | PostgreSQL 16, SQLite 3 | Kimball dimensional modeling (Star Schema, Fact & Dimensions)|
| **Analytics Engineering**| dbt Core (Staging, Intermediate, Marts) | Modular SQL modeling, lineage DAG, singular/schema testing |
| **Orchestration** | Apache Airflow 2.8+ | Directed Acyclic Graph (DAG) scheduling, automated retries |
| **Machine Learning** | Scikit-Learn, SciPy, NumPy | Feature engineering, forward-chaining temporal CV, inference |
| **Data Quality** | Custom Validation Engine, Pytest | Enforcing OHLC consistency, non-positive price filtering |
| **Dashboarding** | Streamlit, Plotly, Seaborn, Matplotlib | Interactive institutional analytics and risk attribution |
| **DevOps & CI/CD** | Docker, Docker Compose, GitHub Actions | Multi-container environment, multi-version CI test matrix |

---

## Business & Financial Objective

Institutional portfolio managers, quantitative analysts, and risk officers require continuous monitoring of cross-asset volatility, tail risk, and structural regime shifts. Traditional monolithic spreadsheets and static notebooks suffer from:
1. **Lookahead Data Leakage:** Overfitting models with future information through unsegmented normalization.
2. **Fragile Data Pipelines:** Failure to detect split errors, corrupted prices, and non-positive spreads.
3. **Siloed Risk Calculations:** Lack of standardized component risk attribution (Euler's theorem) across multi-asset portfolios.

**Solution:** This platform provides a reproducible, automated quantitative infrastructure that ingests live market data, enforces rigorous data quality safeguards, materializes dimensional warehouse models, trains leakage-proof regime classifiers, and delivers interactive multi-horizon risk attribution.

---

## Initial Asset Universe

The platform monitors 16 highly liquid instruments across US equities, broad market indices, commodities, and fixed income configured in `config/assets.yml`:

```yaml
assets:
  # US Equities (Mega-Cap Tech, Energy, Healthcare, Financials)
  - symbol: AAPL   # Apple Inc. (Technology)
  - symbol: MSFT   # Microsoft Corporation (Technology)
  - symbol: NVDA   # NVIDIA Corporation (Technology)
  - symbol: AMZN   # Amazon.com, Inc. (Consumer Discretionary)
  - symbol: GOOGL  # Alphabet Inc. (Communication Services)
  - symbol: META   # Meta Platforms, Inc. (Communication Services)
  - symbol: TSLA   # Tesla, Inc. (Consumer Discretionary)
  - symbol: JPM    # JPMorgan Chase & Co. (Financials)
  - symbol: XOM    # Exxon Mobil Corporation (Energy)
  - symbol: JNJ    # Johnson & Johnson (Healthcare)

  # ETFs & Asset Class Benchmarks
  - symbol: SPY    # SPDR S&P 500 ETF Trust (US Large Cap Benchmark)
  - symbol: QQQ    # Invesco QQQ Trust (Nasdaq-100 Tech Benchmark)
  - symbol: DIA    # SPDR Dow Jones Industrial Average ETF (US Value)
  - symbol: IWM    # iShares Russell 2000 ETF (US Small Cap)
  - symbol: GLD    # SPDR Gold Shares (Precious Metals / Inflation Hedge)
  - symbol: TLT    # iShares 20+ Year Treasury Bond ETF (Fixed Income)
```

---

## Medallion Data Architecture

```
Raw Yahoo API ──> [BRONZE] ──> [VALIDATION] ──> [SILVER] ──> [SPARK] ──> [GOLD] ──> [DWH & ML]
```

1. **Bronze Layer (`data/bronze/`):**
   - Ingests raw OHLCV market feeds from public endpoints.
   - Enriches records with audit metadata: `ingestion_timestamp` (UTC), `source` (`Yahoo Finance`), and `batch_id` (UUIDv4).
   - Saved as immutable Parquet partitions (`bronze_market_data.parquet`) and dual-format CSV.

2. **Silver Layer (`data/silver/`):**
   - Enforces institutional quality gates:
     - Deduplication on `(symbol, date)` natural composite key.
     - Strict non-positive price filtering (`open, high, low, close > 0`).
     - Truncation of negative volumes to zero.
     - OHLC envelope reconciliation: $High \ge \max(Open, Close)$ and $Low \le \min(Open, Close)$.
     - Extreme price anomaly detection ($> +150\%$ or $< -85\%$).
   - Generates automated execution report `reports/data_quality_report.md` (100.0% clean pass rate).

3. **Gold Layer (`data/gold/`):**
   - High-performance feature engineering producing 33 analytical metrics.
   - Computes multi-horizon returns (1D, 5D, 20D, 60D), rolling volatilities, price-to-SMA ratios, volume spikes, drawdowns, and momentum scores.

---

## PySpark & Transformation Strategy

The transformation engine (`src/transformations/spark_transform.py`) utilizes PySpark Window specifications partitioned by `symbol` and ordered by `date`:

```python
window_20d = Window.partitionBy("symbol").orderBy("date").rowsBetween(-19, 0)
window_cumulative = Window.partitionBy("symbol").orderBy("date").rowsBetween(Window.unboundedPreceding, 0)

# 20-Day Rolling Annualized Volatility
df_gold = df_silver.withColumn("volatility_20d", F.stddev("daily_return").over(window_20d) * F.sqrt(F.lit(252)))

# Continuous Peak-to-Trough Drawdown
df_gold = df_gold.withColumn("running_max", F.max("adjusted_close").over(window_cumulative))
df_gold = df_gold.withColumn("drawdown", (F.col("adjusted_close") - F.col("running_max")) / F.col("running_max"))
```

*Dual-Engine Architecture:* When running in local developer environments without an active Java Virtual Machine (JVM), the platform transparently activates a high-performance Vectorized Engine executing identical mathematics in under 0.10s, ensuring 100% reproducibility across both Dockerized Spark clusters and lightweight workstations.

---

## Database & Analytical Star Schema

The platform implements a Kimball Star Schema warehouse (`sql/schema/01_create_market_schema.sql`):

```
                     +---------------------------+
                     |         dim_date          |
                     +---------------------------+
                     | PK date_key (YYYYMMDD)    |
                     |    calendar_date          |
                     |    calendar_year          |
                     |    calendar_quarter       |
                     |    calendar_month         |
                     |    is_trading_day         |
                     +-------------+-------------+
                                   |
                                   | 1
                                   |
                                   | N
+-------------------+ 1         N +--------------------------------+
|     dim_asset     +-------------+       fact_market_daily        |
+-------------------+             +--------------------------------+
| PK  asset_key     |             | PK  fact_key                   |
|     symbol (UK)   |             | FK  market_date_key            |
|     asset_name    |             | FK  asset_key                  |
|     asset_type    |             |     open, high, low, close     |
|     sector        |             |     adjusted_close, volume     |
|     exchange      |             |     daily_return               |
+-------------------+             |     volatility_20d             |
                                  |     sma_20, sma_50, sma_200    |
                                  |     drawdown, is_abnormal_vol  |
                                  +--------------------------------+
```

### Relational Storage Volumes:
- `dim_asset`: 16 configured securities with sector/exchange metadata.
- `dim_date`: 1,254 verified US trading sessions (2021–2025).
- `fact_market_daily`: 20,064 daily fact records with foreign key integrity.

---

## dbt Models & Quality Tests

SQL transformations are organized into dbt Core layers:

1. **Staging Views (`dbt/models/staging/`):**
   - `stg_assets.sql`: Standardizes asset keys, types, and sectors.
   - `stg_market_prices.sql`: Normalizes fact prices and trading dates.

2. **Intermediate Views (`dbt/models/intermediate/`):**
   - `int_daily_returns.sql`: Computes lag-based price deltas.
   - `int_rolling_metrics.sql`: Calculates 20-day, 50-day, and 200-day rolling averages.
   - `int_risk_metrics.sql`: Windowed downside deviation and running peaks.

3. **Marts Tables (`dbt/models/marts/`):**
   - `mart_asset_performance`: Lifetime CAGR, volatility, Sharpe ratio, and total return.
   - `mart_risk_dashboard`: 1-year trailing volatility, current drawdown, and abnormal volume counts.
   - `mart_monthly_performance`: Calendar year and month return matrix.

4. **Automated dbt Tests:**
   - Singular SQL Test: `assert_positive_prices.sql` (Verifies zero non-positive quotes).
   - Singular SQL Test: `assert_valid_drawdown_bounds.sql` (Enforces drawdown $\le 0.0$ and $\ge -1.0$).
   - Schema Tests: `unique` and `not_null` assertions across all dimensions and primary marts.

---

## Financial Analytics & Risk Engine

All financial formulations are rigorously implemented in `src/analytics/`:

### 1. Annualized Sharpe Ratio
$$\text{Sharpe} = \frac{\bar{R}_{\text{daily}} \cdot 252 - R_f}{\sigma_{\text{daily}} \cdot \sqrt{252}}$$
Where $R_f = 0.035$ (3.5% annualized risk-free rate).

### 2. Downside Deviation & Sortino Ratio
$$\sigma_d = \sqrt{252 \cdot \frac{1}{N} \sum_{t=1}^N \min\left(0, R_t - \frac{R_f}{252}\right)^2}$$
$$\text{Sortino} = \frac{\bar{R}_{\text{ann}} - R_f}{\sigma_d}$$

### 3. Maximum Drawdown (MDD) & Recovery Duration
$$\text{DD}_t = \frac{P_t - \max_{\tau \le t} P_\tau}{\max_{\tau \le t} P_\tau}, \quad \text{MDD} = \min_{t} \text{DD}_t$$
Tracks exact peak dates, trough dates, and calendar days until full peak recovery.

### 4. Tail Risk: Value at Risk (VaR) & Conditional VaR (Expected Shortfall)
- **1-Day Historical VaR (95% & 99%):** $-\text{Percentile}(R, 1 - \alpha)$
- **1-Day Parametric Gaussian VaR:** $-(\mu - z_\alpha \cdot \sigma)$
- **Conditional VaR (CVaR):** $-\mathbb{E}\left[ R \mid R \le -\text{VaR}_\alpha \right]$ (Expected loss given a tail breach).

### 5. Multi-Asset Portfolio Risk Decomposition (Euler CCR)
For portfolio volatility $\sigma_p = \sqrt{\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}}$, Euler's homogeneous theorem provides exact additive risk attribution:
$$\text{MCR}_i = \frac{(\mathbf{\Sigma} \mathbf{w})_i}{\sigma_p}, \quad \text{CCR}_i = w_i \cdot \text{MCR}_i, \quad \text{Risk Share}_i = \frac{\text{CCR}_i}{\sigma_p} \times 100\%$$

---

## Machine Learning: Market Regime Classification

### 1. Economic Regime States
1. **Regime 0: Low Vol / Bull (Calm Expansion):** Realized 20D vol $\le$ 252D median vol AND 3M momentum $> 0$.
2. **Regime 1: Low Vol / Stagnant (Grinding Drift):** Low volatility with flat/negative momentum.
3. **Regime 2: High Vol / Bear (Crisis Selloff):** Realized 20D vol $>$ 252D median vol AND 3M momentum $\le 0$.
4. **Regime 3: High Vol / Dynamic Rally (Volatile Rebound):** Elevated volatility with strong positive rebound.

### 2. Zero-Leakage Forward-Chaining Temporal Splits
Financial time series violate i.i.d. assumptions. Random $K$-Fold cross-validation leaks future information into past predictions. The platform enforces strict chronological partitioning:
- **Training Set:** 627 sessions ($\le 2023-12-31$)
- **Validation Set:** 252 sessions ($2024-01-01$ to $2024-12-31$)
- **Out-of-Sample Holdout Test Set:** 249 sessions ($2025-01-01$ to $2025-12-31$)

### 3. Model Benchmark Results (Validation Set 2024)

| Model Architecture | Hyperparameters | Val Accuracy | Val Macro F1 | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline (Majority Class)**| DummyClassifier (Strategy="most_frequent") | 58.33% | 0.3684 | Benchmark |
| **Multinomial Logistic Regression** | $C=1.0$, `l2` penalty, StandardScaler | 82.54% | 0.8024 | Linear Baseline |
| **Random Forest Classifier**| $n=150$, `max_depth=6`, `min_samples_split=5` | 67.06% | 0.5631 | Overfitting |
| **HistGradientBoosting** | `learning_rate=0.05`, `max_iter=150`, `l2=1.0` | **92.46%** | **0.9229** | **Champion** |

### 4. Out-of-Sample Test Set Evaluation (2025 Calendar Year Holdout)
Evaluating the champion `HistGradientBoostingClassifier` on the completely unseen 2025 market environment:
- **Test Accuracy:** **88.76%**
- **Test Macro F1:** **0.6744**
- **Artifact:** Saved to `models/market_regime_model.joblib`
- **Confusion Matrix:** Generated at `reports/figures/regime_confusion_matrix.png`

---

## Key Findings & Market Insights

Analysis of the 1,254 trading sessions across 2021–2025 revealed critical quantitative findings:

1. **Extreme Divergence in Asset Trajectories:**
   - **NVDA** was the universe top performer, generating **+67.4% annualized CAGR** with an exceptional Sharpe ratio of **1.22**, despite exhibiting 48.9% annualized volatility.
   - **TLT** (Long-Term US Treasuries) suffered significant capital destruction (**-7.8% annualized CAGR**, **-44.8% Maximum Drawdown**), failing as an equity diversifier during the 2022–2023 inflation rate hiking cycle.
   - **GLD** (Gold) acted as a resilient hedge, achieving **+12.6% CAGR** with a low 14.1% annualized volatility and Sharpe ratio of **0.86**.

2. **Rejection of Normal Distribution (Fat Tails):**
   - Daily returns across all 16 instruments exhibited universal excess kurtosis ($> 3.0$), with tech equities demonstrating extreme kurtosis ($> 5.5$). Jarque-Bera tests rejected Gaussian normality at $p < 0.0001$.

3. **Portfolio Risk Attribution:**
   - In a balanced model portfolio (35% SPY, 25% QQQ, 20% GLD, 20% TLT), **QQQ and SPY accounted for over 72% of total portfolio risk**, while GLD provided substantial diversification benefits with negative marginal risk contribution during equity market drawdowns.

---

## Interactive Dashboard Guide

The platform exposes an institutional-grade Streamlit portal (`dashboards/app.py`):

1. **Market Overview:** Cross-sectional asset KPI scorecard, 2021–2025 performance leaderboards, and trading day counts.
2. **Single Asset Deep-Dive:** Candlestick charts, 20/50/200 SMA trend overlays, trading volume spikes, and continuous drawdown curves.
3. **Risk Scorecard:** Tabular comparative analysis of Sharpe, Sortino, Downside Deviation, Historical VaR (95%/99%), and CVaR.
4. **Correlation & Co-Movement:** Interactive Pearson and Spearman correlation heatmaps and rolling 60-day pairwise correlations.
5. **Market Regime ML:** Live model inference displaying current regime probabilities, macro signals, and confusion matrix visualizer.
6. **Portfolio Construction & Risk Attribution:** Interactive asset weight sliders with live Euler Component Contribution to Risk (CCR) bar charts.

Launch dashboard:
```bash
streamlit run dashboards/app.py
```

---

## Orchestration & Pipeline Automation

The pipeline is orchestrated via **Apache Airflow** (`airflow/dags/market_data_pipeline.py`):
- **Schedule:** Daily at `00:00 UTC` Monday through Friday (`0 0 * * 1-5`).
- **DAG Workflow:**
  1. `extract_market_data`: Ingests quotes and creates Bronze Layer.
  2. `validate_raw_data`: Applies data quality gates and creates Silver Layer.
  3. `transform_with_spark`: Computes 33 rolling features into Gold Feature Store.
  4. `load_postgres`: Populates Kimball Star Schema dimensions and facts.
  5. `run_dbt_models`: Builds staging, intermediate, and marts tables.
  6. `run_data_quality_checks`: Executes dbt tests and asserts price constraints.
  7. `generate_reports`: Refreshes data quality reports and risk scorecards.

---

## Data Quality & Validation Report

Summary of actual metrics measured during execution:
- **Total Rows Ingested:** 20,064
- **Deduplication:** 0 duplicate rows detected.
- **Null Prices:** 0 missing values in essential OHLC columns.
- **Non-Positive Prices:** 0 instances of zero or negative prices.
- **Negative Volumes:** 0 negative volumes.
- **OHLC Reconciliations:** 0 envelope violations.
- **Clean Silver Rows:** 20,064
- **Quality Pass Rate:** **100.00%**

---

## Testing & CI/CD Pipeline

The platform is fortified with 26 automated unit and regression tests in `tests/`:

```
tests/
├── test_ingestion.py            # Universe configuration and extraction formatting
├── test_validation.py           # Deduplication, bounds, and OHLC reconciliation
├── test_transformations.py      # Vectorized & PySpark window calculations
├── test_financial_metrics.py    # Sharpe, Sortino, VaR, CVaR, and Euler CCR
├── test_ml.py                   # Strict zero-leakage temporal split assertions
└── test_database.py             # Schema DDL, foreign keys, and analytical queries
```

### Running Tests Locally:
```bash
python -m pytest tests/ -v
```
*Result: 26 passed in ~5.9s (100% pass rate).*

### GitHub Actions CI Workflow:
Continuous integration runs on every `push` and `pull_request` across Python 3.11, 3.12, and 3.13, validating syntax, running pytest, compiling dbt models, and testing ML inference.

---

## How to Run

### 1. Prerequisites
- Python 3.11, 3.12, or 3.13
- Git
- (Optional) Docker & Docker Compose for containerized PostgreSQL and Airflow

### 2. Clone and Setup Environment
```bash
git clone https://github.com/MarouaneBizou2004/financial-market-data-platform.git
cd financial-market-data-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Execute End-to-End Pipeline
Run the master runner to execute all stages (ingestion, validation, transformations, warehouse ETL, dbt, and ML):
```bash
python main.py
```

*To skip network ingestion and use local bronze data:*
```bash
python main.py --skip-ingestion
```

### 4. Launch Interactive Streamlit Dashboard
```bash
streamlit run dashboards/app.py
```

---

## Docker & Production Deployment

To run the complete platform stack (PostgreSQL warehouse, Airflow webserver, scheduler, and Streamlit) inside Docker:

```bash
# Start all services
docker-compose up -d

# Verify container health
docker-compose ps
```

- **Airflow Web UI:** `http://localhost:8080` (Credentials: `airflow` / `airflow`)
- **Streamlit Dashboard:** `http://localhost:8501`
- **PostgreSQL Warehouse:** `localhost:5432` (`market_warehouse` / `postgres`)

---

## Project Limitations & Ethical Note

- **Data Attribution:** All market data is retrieved from Yahoo Finance via public API access for research and quantitative evaluation.
- **Analytical & Research Purpose:** This platform is an educational and analytical research framework. **It does NOT provide trading advice or financial recommendations.**
- **Real vs. Derived Data:** The platform strictly distinguishes between observed historical market prices, mathematical risk metrics, and machine learning regime inferences.

---

## Future Enhancements

1. **Intraday Tick Streaming:** Integrating Apache Kafka and WebSockets for real-time order-book streaming.
2. **Hidden Markov Models (HMM):** Implementing unsupervised Gaussian HMMs alongside supervised gradient boosting.
3. **Factor Risk Modeling:** Fama-French 5-factor regression for portfolio alpha/beta decomposition.
4. **Cloud Migration:** Infrastructure as Code (Terraform) templates for AWS EMR and Snowflake.

---

## Author & Contact

**Marouane Bizou**  
- **GitHub:** [@MarouaneBizou2004](https://github.com/MarouaneBizou2004)  
- **Role:** data analyste

---

## Resume / Portfolio Bullet Points

* **Financial Market Data Platform (Python, PySpark, PostgreSQL, dbt, Airflow, Streamlit, ML):**
  - Architected an end-to-end Medallion data platform ingesting and processing 20,000+ daily market quotes across 16 liquid equities and ETFs with 100% data validation pass rates.
  - Implemented scalable PySpark Window transformations computing multi-horizon rolling volatilities, Parkinson range estimators, and continuous peak-to-trough drawdowns.
  - Designed an analytical Kimball Star Schema warehouse in PostgreSQL and orchestrated modular dbt Core transformations across staging, intermediate, and marts layers with singular and schema tests.
  - Developed a supervised machine learning market regime classifier using `HistGradientBoosting`, achieving **88.76% accuracy** and **0.6744 Macro F1** on an unobserved 2025 test set under strict zero-leakage forward-chaining walk-forward validation.
  - Formulated multi-asset portfolio risk decomposition using Euler's Theorem for Component Contribution to Risk (CCR), serving live attribution via an interactive 6-page Streamlit portal.
  - Engineered an Apache Airflow DAG managing 7 automated ETL tasks and established a CI/CD pipeline with GitHub Actions verifying 26 automated unit tests across Python 3.11–3.13.
