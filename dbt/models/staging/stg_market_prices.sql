WITH source AS (
    SELECT * FROM fact_market_daily
),
renamed AS (
    SELECT
        market_date_key AS date_key,
        asset_key,
        CAST(open AS DECIMAL(12, 4)) AS open_price,
        CAST(high AS DECIMAL(12, 4)) AS high_price,
        CAST(low AS DECIMAL(12, 4)) AS low_price,
        CAST(close AS DECIMAL(12, 4)) AS close_price,
        CAST(adjusted_close AS DECIMAL(12, 4)) AS adjusted_close_price,
        CAST(volume AS BIGINT) AS volume,
        CAST(daily_return AS DECIMAL(10, 6)) AS daily_return
    FROM source
)
SELECT * FROM renamed
