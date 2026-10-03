WITH source AS (
    SELECT * FROM dim_asset
),
renamed AS (
    SELECT
        asset_key,
        UPPER(TRIM(symbol)) AS symbol,
        TRIM(asset_name) AS asset_name,
        LOWER(TRIM(asset_type)) AS asset_type,
        TRIM(sector) AS sector,
        TRIM(industry) AS industry,
        currency,
        exchange
    FROM source
)
SELECT * FROM renamed
