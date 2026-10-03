-- Singular test: returns records where drawdown is outside theoretical bounds [0%, -100%]
-- Passes if query returns 0 rows
SELECT
    date_key,
    asset_key,
    drawdown
FROM {{ ref('int_rolling_metrics') }}
WHERE drawdown > 0.001 OR drawdown < -1.0
