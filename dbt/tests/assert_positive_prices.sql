-- Singular test: returns records where close price is non-positive
-- Passes if query returns 0 rows
SELECT
    date_key,
    asset_key,
    close_price
FROM {{ ref('stg_market_prices') }}
WHERE close_price <= 0
