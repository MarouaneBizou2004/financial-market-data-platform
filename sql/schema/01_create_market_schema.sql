-- ==============================================================================
-- Analytical Financial Data Warehouse Schema (Star Schema)
-- Engine: ANSI SQL, PostgreSQL & SQLite Compatible
-- Grain: One row per tradeable asset per trading day in fact_market_daily
-- ==============================================================================

-- Drop tables in reverse foreign key order
DROP TABLE IF EXISTS fact_market_daily;
DROP TABLE IF EXISTS dim_asset;
DROP TABLE IF EXISTS dim_date;

-- ==============================================================================
-- DIMENSION: dim_asset
-- Grain: One row per unique asset/security
-- ==============================================================================
CREATE TABLE dim_asset (
    asset_key INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    asset_name VARCHAR(100) NOT NULL,
    asset_type VARCHAR(20) NOT NULL,          -- 'equity', 'etf', 'commodity', 'fixed_income'
    sector VARCHAR(50) NOT NULL,
    industry VARCHAR(50) NOT NULL,
    currency VARCHAR(5) NOT NULL DEFAULT 'USD',
    exchange VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_asset_symbol ON dim_asset(symbol);
CREATE INDEX idx_dim_asset_type ON dim_asset(asset_type);
CREATE INDEX idx_dim_asset_sector ON dim_asset(sector);

-- ==============================================================================
-- DIMENSION: dim_date
-- Grain: One row per calendar day
-- ==============================================================================
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,             -- Smart key YYYYMMDD (e.g. 20240102)
    calendar_date DATE NOT NULL UNIQUE,       -- ISO YYYY-MM-DD
    calendar_year INTEGER NOT NULL,
    calendar_quarter INTEGER NOT NULL,
    calendar_month INTEGER NOT NULL,
    calendar_week INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,             -- 1 = Monday, 7 = Sunday
    day_name VARCHAR(15) NOT NULL,
    is_trading_day BOOLEAN NOT NULL DEFAULT 1,
    is_month_end BOOLEAN NOT NULL DEFAULT 0,
    is_quarter_end BOOLEAN NOT NULL DEFAULT 0
);

CREATE INDEX idx_dim_date_calendar ON dim_date(calendar_date);
CREATE INDEX idx_dim_date_year ON dim_date(calendar_year);

-- ==============================================================================
-- FACT: fact_market_daily
-- Grain: EXACTLY ONE ROW PER ASSET PER TRADING DAY
-- ==============================================================================
CREATE TABLE fact_market_daily (
    market_date_key INTEGER NOT NULL,
    asset_key INTEGER NOT NULL,
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    adjusted_close DECIMAL(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    daily_return DECIMAL(10, 6),
    return_5d DECIMAL(10, 6),
    return_20d DECIMAL(10, 6),
    volatility_20d DECIMAL(10, 6),
    volatility_60d DECIMAL(10, 6),
    sma_20 DECIMAL(12, 4),
    sma_50 DECIMAL(12, 4),
    sma_200 DECIMAL(12, 4),
    drawdown DECIMAL(10, 6),
    is_abnormal_volume BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (market_date_key, asset_key),
    FOREIGN KEY (market_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (asset_key) REFERENCES dim_asset(asset_key)
);

CREATE INDEX idx_fact_daily_asset ON fact_market_daily(asset_key);
CREATE INDEX idx_fact_daily_date ON fact_market_daily(market_date_key);
CREATE INDEX idx_fact_daily_return ON fact_market_daily(daily_return);
