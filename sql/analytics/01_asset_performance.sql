-- ==============================================================================
-- Query 01: Asset Performance & Risk-Adjusted Return Summary
-- Purpose: Evaluates long-term cumulative return, annualized CAGR, volatility, and Sharpe.
-- Grain: One row per asset
-- ==============================================================================

WITH asset_bounds AS (
    SELECT
        a.asset_key,
        a.symbol,
        a.asset_name,
        a.asset_type,
        a.sector,
        MIN(f.market_date_key) AS first_date_key,
        MAX(f.market_date_key) AS last_date_key,
        COUNT(f.market_date_key) AS total_trading_days,
        AVG(f.daily_return) AS avg_daily_return,
        -- Sample standard deviation of daily returns
        -- In SQLite: sqrt(avg(r^2) - avg(r)^2)
        SQRT(AVG(f.daily_return * f.daily_return) - (AVG(f.daily_return) * AVG(f.daily_return))) AS daily_stddev
    FROM dim_asset a
    JOIN fact_market_daily f ON a.asset_key = f.asset_key
    GROUP BY a.asset_key, a.symbol, a.asset_name, a.asset_type, a.sector
),
asset_prices AS (
    SELECT
        ab.asset_key,
        ab.symbol,
        ab.asset_name,
        ab.asset_type,
        ab.sector,
        ab.total_trading_days,
        ab.avg_daily_return,
        ab.daily_stddev,
        f_start.adjusted_close AS initial_price,
        f_end.adjusted_close AS latest_price
    FROM asset_bounds ab
    JOIN fact_market_daily f_start ON ab.asset_key = f_start.asset_key AND ab.first_date_key = f_start.market_date_key
    JOIN fact_market_daily f_end ON ab.asset_key = f_end.asset_key AND ab.last_date_key = f_end.market_date_key
)
SELECT
    symbol,
    asset_name,
    asset_type,
    sector,
    total_trading_days,
    ROUND(initial_price, 2) AS initial_price,
    ROUND(latest_price, 2) AS latest_price,
    ROUND(((latest_price - initial_price) / initial_price) * 100.0, 2) AS total_return_pct,
    -- Annualized CAGR % = ((latest / initial) ^ (252 / days) - 1) * 100
    -- Approximated using continuous compound formula in SQL
    ROUND(((latest_price - initial_price) / initial_price) / (total_trading_days / 252.0) * 100.0, 2) AS annualized_return_pct,
    ROUND(daily_stddev * SQRT(252.0) * 100.0, 2) AS annualized_volatility_pct,
    -- Sharpe Ratio assuming 3.5% risk free rate
    ROUND(((avg_daily_return * 252.0) - 0.035) / NULLIF(daily_stddev * SQRT(252.0), 0), 2) AS sharpe_ratio
FROM asset_prices
ORDER BY total_return_pct DESC;
