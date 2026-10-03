# Comprehensive Data Dictionary
## Financial Market Data Platform

### 1. Medallion Storage Layer Specifications

#### 1.1 Bronze Layer (`data/bronze/bronze_market_data.parquet`)
*Grain: One raw quote per asset per trading session.*

| Column Name | Data Type | Nullable | Source | Description |
| :--- | :--- | :--- | :--- | :--- |
| `symbol` | `VARCHAR(10)` | No | API | Standard ticker symbol (e.g. `AAPL`, `SPY`) |
| `date` | `VARCHAR(10)` | No | API | ISO 8601 calendar date (`YYYY-MM-DD`) |
| `open` | `FLOAT64` | No | API | Unadjusted session opening price (USD) |
| `high` | `FLOAT64` | No | API | Unadjusted session maximum price (USD) |
| `low` | `FLOAT64` | No | API | Unadjusted session minimum price (USD) |
| `close` | `FLOAT64` | No | API | Unadjusted session closing price (USD) |
| `adjusted_close` | `FLOAT64` | No | API | Split- and dividend-adjusted closing price (USD) |
| `volume` | `INT64` | No | API | Total shares/contracts transacted during session |
| `ingestion_timestamp`| `VARCHAR(30)` | No | ETL | UTC timestamp when record was collected |
| `source` | `VARCHAR(50)` | No | ETL | Data provider designation (`Yahoo Finance`) |
| `batch_id` | `VARCHAR(36)` | No | ETL | UUIDv4 tracking the ingestion job execution run |

---

#### 1.2 Silver Layer (`data/silver/silver_market_data.parquet`)
*Grain: One validated, deduplicated quote per asset per trading session.*

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `symbol` | `VARCHAR(10)` | `NOT NULL, UPPER` | Normalized uppercase ticker |
| `date` | `VARCHAR(10)` | `NOT NULL, ISO` | Trading date |
| `open` | `FLOAT64` | `> 0.0` | Validated positive opening price |
| `high` | `FLOAT64` | `high >= max(open, close)` | Reconciled session upper envelope |
| `low` | `FLOAT64` | `low <= min(open, close)` | Reconciled session lower envelope |
| `close` | `FLOAT64` | `> 0.0` | Validated positive closing price |
| `adjusted_close` | `FLOAT64` | `> 0.0` | Validated adjusted closing price |
| `volume` | `INT64` | `>= 0` | Truncated non-negative trading volume |

---

#### 1.3 Gold Layer (`data/gold/gold_market_features.parquet`)
*Grain: One feature-engineered analytical row per asset per trading session.*

| Column Name | Data Type | Calculation / Formula | Business Meaning |
| :--- | :--- | :--- | :--- |
| `daily_return` | `FLOAT64` | $(P_t - P_{t-1}) / P_{t-1}$ | 1-Day Arithmetic Price Return |
| `log_return` | `FLOAT64` | $\ln(P_t / P_{t-1})$ | 1-Day Continuously Compounded Log Return |
| `return_5d` | `FLOAT64` | $(P_t - P_{t-5}) / P_{t-5}$ | 1-Week (5-Day) Cumulative Return |
| `return_20d` | `FLOAT64` | $(P_t - P_{t-20}) / P_{t-20}$ | 1-Month (20-Day) Cumulative Return |
| `return_60d` | `FLOAT64` | $(P_t - P_{t-60}) / P_{t-60}$ | 1-Quarter (60-Day) Cumulative Return |
| `volatility_20d` | `FLOAT64` | $\text{std}(R_{20}) \times \sqrt{252}$ | Annualized 20-Day Rolling Realized Volatility |
| `volatility_60d` | `FLOAT64` | $\text{std}(R_{60}) \times \sqrt{252}$ | Annualized 60-Day Rolling Realized Volatility |
| `sma_20` | `FLOAT64` | $\text{mean}(P_{t-19 \dots t})$ | 20-Day Simple Moving Average |
| `sma_50` | `FLOAT64` | $\text{mean}(P_{t-49 \dots t})$ | 50-Day Intermediate Trend SMA |
| `sma_200` | `FLOAT64` | $\text{mean}(P_{t-199 \dots t})$ | 200-Day Long-Term Trend SMA |
| `sma_20_ratio` | `FLOAT64` | $P_t / \text{sma}_{20}$ | Price relative to 20-day trend |
| `sma_50_ratio` | `FLOAT64` | $P_t / \text{sma}_{50}$ | Price relative to 50-day trend |
| `sma_200_ratio` | `FLOAT64` | $P_t / \text{sma}_{200}$ | Price relative to 200-day trend (> 1.0 = Bull) |
| `avg_volume_20d`| `FLOAT64` | $\text{mean}(\text{Vol}_{20})$ | 20-Day Baseline Average Volume |
| `volume_ratio` | `FLOAT64` | $\text{Vol}_t / \text{avg\_vol}_{20}$ | Relative volume activity factor |
| `is_abnormal_volume`| `BOOLEAN`| $\text{volume\_ratio} > 2.0$ | Flag indicating volume surge $\ge 200\%$ of normal |
| `rolling_max_close` | `FLOAT64`| $\max_{\tau \le t} P_\tau$ | Historical peak closing price up to day $t$ |
| `drawdown` | `FLOAT64` | $(P_t - \text{Peak}_t) / \text{Peak}_t$| Current peak-to-trough decline ($\in [-1.0, 0.0]$) |
| `momentum_1m` | `FLOAT64` | $(P_t - P_{t-21}) / P_{t-21}$ | 1-Month Cross-Sectional Momentum Score |
| `momentum_3m` | `FLOAT64` | $(P_t - P_{t-63}) / P_{t-63}$ | 3-Month Cross-Sectional Momentum Score |
| `momentum_6m` | `FLOAT64` | $(P_t - P_{t-126}) / P_{t-126}$| 6-Month Cross-Sectional Momentum Score |
| `momentum_12m` | `FLOAT64` | $(P_t - P_{t-252}) / P_{t-252}$| 12-Month Cross-Sectional Momentum Score |
| `cumulative_return`| `FLOAT64` | $\prod(1 + R) - 1$ | Compounded lifetime return from series inception |

---

### 2. Analytical Warehouse Relational Star Schema

#### 2.1 Table: `dim_asset`
*Primary Key: `asset_key` (Surrogate Integer)*

| Column | Type | Nullable | Key | Description |
| :--- | :--- | :--- | :--- | :--- |
| `asset_key` | `INTEGER` | No | PK | Auto-incrementing surrogate surrogate key |
| `symbol` | `VARCHAR(10)` | No | UK | Ticker symbol (e.g. `NVDA`) |
| `asset_name` | `VARCHAR(100)`| No | | Full company or fund name |
| `asset_type` | `VARCHAR(20)` | No | | Security type: `equity`, `etf` |
| `sector` | `VARCHAR(50)` | No | | Macro industry classification (e.g. `Technology`) |
| `industry` | `VARCHAR(50)` | No | | Sub-industry classification |
| `currency` | `VARCHAR(5)` | No | | Base currency (`USD`) |
| `exchange` | `VARCHAR(20)` | No | | Listing exchange (`NASDAQ`, `NYSE`) |
| `created_at` | `TIMESTAMP` | No | | Timestamp when asset was dimensionally registered |

#### 2.2 Table: `dim_date`
*Primary Key: `date_key` (Smart Integer YYYYMMDD)*

| Column | Type | Nullable | Key | Description |
| :--- | :--- | :--- | :--- | :--- |
| `date_key` | `INTEGER` | No | PK | Smart key in format `20240102` |
| `calendar_date` | `DATE` | No | UK | Standard ISO 8601 calendar date |
| `calendar_year` | `INTEGER` | No | | 4-digit calendar year (e.g. `2024`) |
| `calendar_quarter`| `INTEGER` | No | | Calendar quarter (1 to 4) |
| `calendar_month` | `INTEGER` | No | | Calendar month (1 to 12) |
| `calendar_week` | `INTEGER` | No | | ISO week number (1 to 53) |
| `day_of_week` | `INTEGER` | No | | Day of week (1 = Monday, 7 = Sunday) |
| `day_name` | `VARCHAR(15)` | No | | English day name (`Monday`, `Tuesday`, etc.) |
| `is_trading_day`| `BOOLEAN` | No | | 1 if public markets were open, 0 if closed |
| `is_month_end` | `BOOLEAN` | No | | 1 if date is final trading day of calendar month |
| `is_quarter_end`| `BOOLEAN` | No | | 1 if date is final trading day of quarter |

#### 2.3 Table: `fact_market_daily`
*Primary Key: `fact_key` (Surrogate Integer)*

| Column | Type | Nullable | Key | Description |
| :--- | :--- | :--- | :--- | :--- |
| `fact_key` | `INTEGER` | No | PK | Auto-incrementing surrogate fact key |
| `market_date_key` | `INTEGER` | No | FK | References `dim_date.date_key` |
| `asset_key` | `INTEGER` | No | FK | References `dim_asset.asset_key` |
| `open` | `DECIMAL(12,4)`| No | | Opening price |
| `high` | `DECIMAL(12,4)`| No | | Session high price |
| `low` | `DECIMAL(12,4)`| No | | Session low price |
| `close` | `DECIMAL(12,4)`| No | | Closing price |
| `adjusted_close`| `DECIMAL(12,4)`| No | | Corporate-action adjusted price |
| `volume` | `BIGINT` | No | | Trading volume |
| `daily_return` | `DECIMAL(8,6)` | Yes | | 1-Day price percentage return |
| `volatility_20d`| `DECIMAL(8,6)` | Yes | | 20-Day annualized volatility |
| `sma_20` | `DECIMAL(12,4)`| Yes | | 20-Day simple moving average |
| `sma_50` | `DECIMAL(12,4)`| Yes | | 50-Day simple moving average |
| `sma_200` | `DECIMAL(12,4)`| Yes | | 200-Day simple moving average |
| `drawdown` | `DECIMAL(8,6)` | Yes | | Peak-to-trough decline |

---

### 3. dbt Data Marts

#### 3.1 Model: `mart_asset_performance`
- **Grain:** One row per asset representing lifetime aggregate statistics.
- **Columns:** `symbol`, `asset_name`, `asset_type`, `sector`, `total_trading_days`, `initial_price`, `latest_price`, `total_return_pct`, `annualized_return_pct`, `annualized_volatility_pct`, `sharpe_ratio`.

#### 3.2 Model: `mart_risk_dashboard`
- **Grain:** One row per asset representing 1-year trailing risk metrics.
- **Columns:** `symbol`, `asset_name`, `sector`, `trailing_1y_volatility_pct`, `max_drawdown_pct`, `current_drawdown_pct`, `abnormal_volume_days_1y`, `latest_sma_200_ratio`, `trend_signal`.

#### 3.3 Model: `mart_monthly_performance`
- **Grain:** One row per asset per calendar month.
- **Columns:** `symbol`, `calendar_year`, `calendar_month`, `month_open_price`, `month_close_price`, `monthly_return_pct`.
