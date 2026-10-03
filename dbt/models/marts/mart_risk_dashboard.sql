WITH assets AS (
    SELECT * FROM {{ ref('stg_assets') }}
),
risk AS (
    SELECT * FROM {{ ref('int_risk_metrics') }}
),
mdd AS (
    SELECT
        asset_key,
        MIN(drawdown) AS max_drawdown
    FROM {{ ref('int_rolling_metrics') }}
    GROUP BY asset_key
)
SELECT
    a.symbol,
    a.asset_name,
    a.sector,
    r.sharpe_ratio,
    r.sortino_ratio,
    ROUND(r.annualized_volatility * 100.0, 2) AS annualized_volatility_pct,
    ROUND(r.annualized_downside_deviation * 100.0, 2) AS downside_deviation_pct,
    ROUND(mdd.max_drawdown * 100.0, 2) AS max_drawdown_pct,
    DENSE_RANK() OVER (ORDER BY r.sharpe_ratio DESC) AS sharpe_rank,
    DENSE_RANK() OVER (ORDER BY r.annualized_volatility ASC) AS defensive_rank
FROM assets a
JOIN risk r ON a.asset_key = r.asset_key
JOIN mdd ON a.asset_key = mdd.asset_key
