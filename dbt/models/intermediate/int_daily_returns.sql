WITH prices AS (
    SELECT * FROM {{ ref('stg_market_prices') }}
),
lagged AS (
    SELECT
        date_key,
        asset_key,
        close_price,
        volume,
        daily_return,
        LAG(close_price, 5) OVER (PARTITION BY asset_key ORDER BY date_key) AS close_5d_ago,
        LAG(close_price, 20) OVER (PARTITION BY asset_key ORDER BY date_key) AS close_20d_ago
    FROM prices
)
SELECT
    date_key,
    asset_key,
    close_price,
    volume,
    daily_return,
    ROUND((close_price - close_5d_ago) * 1.0 / NULLIF(close_5d_ago, 0), 6) AS return_5d,
    ROUND((close_price - close_20d_ago) * 1.0 / NULLIF(close_20d_ago, 0), 6) AS return_20d
FROM lagged
