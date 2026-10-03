-- ==============================================================================
-- Query 04: Maximum Drawdown & Downside Recovery Analysis
-- Purpose: Identifies catastrophic historical pullbacks and current drawdown status.
-- Grain: One row per asset
-- ==============================================================================

WITH drawdown_summary AS (
    SELECT
        a.symbol,
        a.asset_name,
        a.sector,
        MIN(f.drawdown) AS max_drawdown,
        AVG(f.drawdown) AS avg_drawdown,
        -- Current drawdown at latest available date
        (
            SELECT f_latest.drawdown
            FROM fact_market_daily f_latest
            JOIN dim_date d_latest ON f_latest.market_date_key = d_latest.date_key
            WHERE f_latest.asset_key = a.asset_key
            ORDER BY d_latest.calendar_date DESC
            LIMIT 1
        ) AS current_drawdown,
        -- Date when max drawdown trough occurred
        (
            SELECT d_min.calendar_date
            FROM fact_market_daily f_min
            JOIN dim_date d_min ON f_min.market_date_key = d_min.date_key
            WHERE f_min.asset_key = a.asset_key
            ORDER BY f_min.drawdown ASC
            LIMIT 1
        ) AS max_drawdown_trough_date
    FROM dim_asset a
    JOIN fact_market_daily f ON a.asset_key = f.asset_key
    GROUP BY a.asset_key, a.symbol, a.asset_name, a.sector
)
SELECT
    symbol,
    asset_name,
    sector,
    ROUND(max_drawdown * 100.0, 2) AS max_drawdown_pct,
    max_drawdown_trough_date,
    ROUND(avg_drawdown * 100.0, 2) AS average_drawdown_pct,
    ROUND(current_drawdown * 100.0, 2) AS current_drawdown_pct,
    CASE
        WHEN current_drawdown >= -0.02 THEN 'At or Near All-Time High'
        WHEN current_drawdown >= -0.10 THEN 'Minor Pullback (2% - 10%)'
        WHEN current_drawdown >= -0.20 THEN 'Correction (10% - 20%)'
        ELSE 'Bear Market State (> 20% drawdown)'
    END AS technical_status
FROM drawdown_summary
ORDER BY max_drawdown ASC;
