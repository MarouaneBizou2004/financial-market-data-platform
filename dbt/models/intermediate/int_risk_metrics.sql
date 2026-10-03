WITH returns_source AS (
    SELECT * FROM {{ ref('int_daily_returns') }}
),
asset_aggregates AS (
    SELECT
        asset_key,
        COUNT(daily_return) AS trading_days,
        AVG(daily_return) AS mean_daily_return,
        SQRT(AVG(daily_return * daily_return) - (AVG(daily_return) * AVG(daily_return))) AS daily_volatility,
        SQRT(
            SUM(CASE WHEN daily_return < 0 THEN daily_return * daily_return ELSE 0 END) /
            NULLIF(COUNT(daily_return), 0)
        ) AS daily_downside_deviation
    FROM returns_source
    WHERE daily_return IS NOT NULL
    GROUP BY asset_key
)
SELECT
    asset_key,
    trading_days,
    ROUND(mean_daily_return * 252.0, 6) AS annualized_return,
    ROUND(daily_volatility * SQRT(252.0), 6) AS annualized_volatility,
    ROUND(daily_downside_deviation * SQRT(252.0), 6) AS annualized_downside_deviation,
    ROUND(((mean_daily_return * 252.0) - 0.035) / NULLIF(daily_volatility * SQRT(252.0), 0), 4) AS sharpe_ratio,
    ROUND(((mean_daily_return * 252.0) - 0.035) / NULLIF(daily_downside_deviation * SQRT(252.0), 0), 4) AS sortino_ratio
FROM asset_aggregates
