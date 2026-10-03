-- ==============================================================================
-- Query 06: Macro Sector & Asset Class Performance
-- Purpose: Aggregates returns, volatility, and volume across economic sectors and ETF classes.
-- Grain: One row per sector
-- ==============================================================================

WITH sector_daily AS (
    SELECT
        a.sector,
        d.calendar_date,
        COUNT(DISTINCT a.symbol) AS assets_in_sector,
        AVG(f.daily_return) AS sector_daily_return,
        SUM(f.volume) AS sector_total_volume
    FROM dim_asset a
    JOIN fact_market_daily f ON a.asset_key = f.asset_key
    JOIN dim_date d ON f.market_date_key = d.date_key
    GROUP BY a.sector, d.calendar_date
),
sector_stats AS (
    SELECT
        sector,
        MAX(assets_in_sector) AS asset_count,
        COUNT(calendar_date) AS total_trading_days,
        AVG(sector_daily_return) AS mean_daily_return,
        SQRT(AVG(sector_daily_return * sector_daily_return) - (AVG(sector_daily_return) * AVG(sector_daily_return))) AS sector_daily_stddev,
        AVG(sector_total_volume) AS avg_daily_volume
    FROM sector_daily
    GROUP BY sector
)
SELECT
    sector,
    asset_count,
    ROUND(mean_daily_return * 252.0 * 100.0, 2) AS annualized_return_pct,
    ROUND(sector_daily_stddev * SQRT(252.0) * 100.0, 2) AS annualized_volatility_pct,
    ROUND(((mean_daily_return * 252.0) - 0.035) / NULLIF(sector_daily_stddev * SQRT(252.0), 0), 2) AS sector_sharpe_ratio,
    ROUND(avg_daily_volume / 1000000.0, 2) AS avg_daily_volume_millions
FROM sector_stats
ORDER BY sector_sharpe_ratio DESC;
