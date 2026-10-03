WITH base_returns AS (
    SELECT * FROM {{ ref('int_daily_returns') }}
),
rolling_calcs AS (
    SELECT
        date_key,
        asset_key,
        close_price,
        volume,
        daily_return,
        return_5d,
        return_20d,
        AVG(close_price) OVER (
            PARTITION BY asset_key
            ORDER BY date_key
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS sma_20,
        AVG(close_price) OVER (
            PARTITION BY asset_key
            ORDER BY date_key
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        ) AS sma_50,
        AVG(close_price) OVER (
            PARTITION BY asset_key
            ORDER BY date_key
            ROWS BETWEEN 199 PRECEDING AND CURRENT ROW
        ) AS sma_200,
        AVG(volume) OVER (
            PARTITION BY asset_key
            ORDER BY date_key
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS avg_volume_20d,
        MAX(close_price) OVER (
            PARTITION BY asset_key
            ORDER BY date_key
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS rolling_max_close
    FROM base_returns
)
SELECT
    date_key,
    asset_key,
    close_price,
    volume,
    daily_return,
    return_5d,
    return_20d,
    ROUND(sma_20, 4) AS sma_20,
    ROUND(sma_50, 4) AS sma_50,
    ROUND(sma_200, 4) AS sma_200,
    ROUND(close_price / NULLIF(sma_20, 0), 4) AS sma_20_ratio,
    ROUND(close_price / NULLIF(sma_50, 0), 4) AS sma_50_ratio,
    ROUND(close_price / NULLIF(sma_200, 0), 4) AS sma_200_ratio,
    ROUND(volume * 1.0 / NULLIF(avg_volume_20d, 0), 2) AS volume_ratio,
    ROUND((close_price - rolling_max_close) / NULLIF(rolling_max_close, 0), 6) AS drawdown
FROM rolling_calcs
