-- ==============================================================================
-- Query 08: Value at Risk (VaR), Downside Deviation & Tail Risk Scorecard
-- Purpose: Quantifies severe downside loss exposure and tail risk across all assets.
-- Grain: One row per asset
-- ==============================================================================

WITH asset_downside AS (
    SELECT
        a.symbol,
        a.asset_name,
        a.sector,
        COUNT(f.daily_return) AS total_trading_days,
        AVG(f.daily_return) AS mean_daily_return,
        MIN(f.daily_return) AS worst_single_day_return,
        -- Downside deviation: RMS of negative returns below 0
        SQRT(
            SUM(CASE WHEN f.daily_return < 0 THEN f.daily_return * f.daily_return ELSE 0 END) /
            NULLIF(COUNT(f.daily_return), 0)
        ) AS daily_downside_deviation,
        -- Standard deviation
        SQRT(AVG(f.daily_return * f.daily_return) - (AVG(f.daily_return) * AVG(f.daily_return))) AS daily_stddev
    FROM dim_asset a
    JOIN fact_market_daily f ON a.asset_key = f.asset_key
    GROUP BY a.asset_key, a.symbol, a.asset_name, a.sector
),
ranked_returns AS (
    SELECT
        a.symbol,
        f.daily_return,
        ROW_NUMBER() OVER (PARTITION BY a.symbol ORDER BY f.daily_return ASC) AS row_num,
        COUNT(*) OVER (PARTITION BY a.symbol) AS total_rows
    FROM dim_asset a
    JOIN fact_market_daily f ON a.asset_key = f.asset_key
    WHERE f.daily_return IS NOT NULL
),
var_95 AS (
    -- 5th percentile return (Historical 95% VaR)
    SELECT
        symbol,
        daily_return AS var_95_daily
    FROM ranked_returns
    WHERE row_num = CAST(ROUND(total_rows * 0.05) AS INTEGER)
)
SELECT
    ad.symbol,
    ad.asset_name,
    ad.sector,
    -- 95% 1-Day Historical VaR (expressed as positive % loss threshold)
    ROUND(ABS(v.var_95_daily) * 100.0, 2) AS var_95_daily_pct,
    ROUND(ad.worst_single_day_return * 100.0, 2) AS worst_single_day_pct,
    ROUND(ad.daily_downside_deviation * SQRT(252.0) * 100.0, 2) AS annualized_downside_deviation_pct,
    -- Sortino Ratio: (Annualized Return - 3.5% Rf) / Annualized Downside Deviation
    ROUND(
        ((ad.mean_daily_return * 252.0) - 0.035) /
        NULLIF(ad.daily_downside_deviation * SQRT(252.0), 0),
        2
    ) AS sortino_ratio,
    CASE
        WHEN ABS(v.var_95_daily) > 0.025 THEN 'High Tail Risk (> 2.5% daily VaR)'
        WHEN ABS(v.var_95_daily) > 0.015 THEN 'Moderate Tail Risk (1.5% - 2.5%)'
        ELSE 'Low Tail Risk (< 1.5% daily VaR)'
    END AS tail_risk_classification
FROM asset_downside ad
JOIN var_95 v ON ad.symbol = v.symbol
ORDER BY var_95_daily_pct DESC;
