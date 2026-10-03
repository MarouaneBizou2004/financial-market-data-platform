-- ==============================================================================
-- Query 03: Cross-Sectional Volatility Ranking
-- Purpose: Identifies most volatile and defensive assets across trailing windows.
-- Grain: One row per asset
-- ==============================================================================

WITH latest_volatilities AS (
    SELECT
        a.symbol,
        a.asset_name,
        a.asset_type,
        a.sector,
        f.volatility_20d,
        f.volatility_60d,
        d.calendar_date,
        ROW_NUMBER() OVER (PARTITION BY a.symbol ORDER BY d.calendar_date DESC) AS rn
    FROM dim_asset a
    JOIN fact_market_daily f ON a.asset_key = f.asset_key
    JOIN dim_date d ON f.market_date_key = d.date_key
    WHERE f.volatility_20d IS NOT NULL
)
SELECT
    DENSE_RANK() OVER (ORDER BY volatility_20d DESC) AS rank_20d,
    symbol,
    asset_name,
    asset_type,
    sector,
    ROUND(volatility_20d * 100.0, 2) AS annualized_volatility_20d_pct,
    ROUND(volatility_60d * 100.0, 2) AS annualized_volatility_60d_pct,
    calendar_date AS as_of_date,
    CASE
        WHEN volatility_20d > 0.35 THEN 'High Risk / Hyper-Volatile'
        WHEN volatility_20d > 0.20 THEN 'Moderate Risk / Core Equity'
        ELSE 'Defensive / Low Volatility'
    END AS volatility_regime_classification
FROM latest_volatilities
WHERE rn = 1
ORDER BY rank_20d ASC;
