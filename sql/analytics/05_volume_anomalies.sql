-- ==============================================================================
-- Query 05: Volume Anomalies & Institutional Liquidity Surges
-- Purpose: Detects days with trading volume > 200% of 20-day moving average volume.
-- Grain: One row per anomalous asset-day
-- ==============================================================================

WITH volume_spikes AS (
    SELECT
        a.symbol,
        a.asset_name,
        a.sector,
        d.calendar_date,
        f.close,
        f.volume,
        f.daily_return,
        f.sma_20,
        f.is_abnormal_volume,
        -- Trailing 20-day average volume calculated via window
        AVG(f.volume) OVER (
            PARTITION BY f.asset_key
            ORDER BY d.calendar_date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS avg_volume_20d
    FROM dim_asset a
    JOIN fact_market_daily f ON a.asset_key = f.asset_key
    JOIN dim_date d ON f.market_date_key = d.date_key
),
flagged_spikes AS (
    SELECT
        symbol,
        asset_name,
        sector,
        calendar_date,
        close,
        volume,
        ROUND(avg_volume_20d, 0) AS avg_volume_20d,
        ROUND((volume * 1.0) / NULLIF(avg_volume_20d, 0), 2) AS volume_ratio,
        ROUND(daily_return * 100.0, 2) AS daily_return_pct,
        CASE
            WHEN daily_return > 0.03 AND (volume * 1.0) / NULLIF(avg_volume_20d, 0) > 2.0 THEN 'Institutional Accumulation (Surge Up)'
            WHEN daily_return < -0.03 AND (volume * 1.0) / NULLIF(avg_volume_20d, 0) > 2.0 THEN 'Institutional Capitulation (Heavy Selloff)'
            WHEN (volume * 1.0) / NULLIF(avg_volume_20d, 0) > 2.0 THEN 'High Volume Consolidation'
            ELSE 'Normal Volume'
        END AS anomaly_signal
    FROM volume_spikes
    WHERE (volume * 1.0) / NULLIF(avg_volume_20d, 0) > 2.0
)
SELECT
    calendar_date,
    symbol,
    asset_name,
    volume,
    avg_volume_20d,
    volume_ratio,
    daily_return_pct,
    anomaly_signal
FROM flagged_spikes
ORDER BY volume_ratio DESC
LIMIT 50;
