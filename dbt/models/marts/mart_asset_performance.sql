WITH assets AS (
    SELECT * FROM {{ ref('stg_assets') }}
),
risk AS (
    SELECT * FROM {{ ref('int_risk_metrics') }}
),
latest_metrics AS (
    SELECT
        asset_key,
        close_price AS latest_price,
        drawdown AS current_drawdown,
        sma_200_ratio,
        ROW_NUMBER() OVER (PARTITION BY asset_key ORDER BY date_key DESC) AS rn
    FROM {{ ref('int_rolling_metrics') }}
)
SELECT
    a.symbol,
    a.asset_name,
    a.asset_type,
    a.sector,
    a.industry,
    lm.latest_price,
    ROUND(r.annualized_return * 100.0, 2) AS annualized_return_pct,
    ROUND(r.annualized_volatility * 100.0, 2) AS annualized_volatility_pct,
    r.sharpe_ratio,
    r.sortino_ratio,
    ROUND(lm.current_drawdown * 100.0, 2) AS current_drawdown_pct,
    lm.sma_200_ratio
FROM assets a
JOIN risk r ON a.asset_key = r.asset_key
JOIN latest_metrics lm ON a.asset_key = lm.asset_key AND lm.rn = 1
