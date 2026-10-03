-- ==============================================================================
-- Query 07: Benchmark Beta & Market Correlation Summary
-- Purpose: Quantifies systematic risk (Beta) and co-movement relative to SPY.
-- Formula: Beta = Cov(R_i, R_m) / Var(R_m)
-- Grain: One row per asset
-- ==============================================================================

WITH benchmark_returns AS (
    SELECT
        f.market_date_key,
        f.daily_return AS spy_return
    FROM fact_market_daily f
    JOIN dim_asset a ON f.asset_key = a.asset_key
    WHERE a.symbol = 'SPY'
),
asset_joined AS (
    SELECT
        a.symbol,
        a.asset_name,
        a.sector,
        f.daily_return AS asset_return,
        b.spy_return
    FROM dim_asset a
    JOIN fact_market_daily f ON a.asset_key = f.asset_key
    JOIN benchmark_returns b ON f.market_date_key = b.market_date_key
    WHERE f.daily_return IS NOT NULL AND b.spy_return IS NOT NULL
),
beta_calc AS (
    SELECT
        symbol,
        asset_name,
        sector,
        COUNT(*) AS obs_count,
        AVG(asset_return) AS mean_asset,
        AVG(spy_return) AS mean_spy,
        -- Covariance = E[R_i * R_m] - E[R_i] * E[R_m]
        AVG(asset_return * spy_return) - (AVG(asset_return) * AVG(spy_return)) AS cov_asset_spy,
        -- Variance = E[R_m^2] - E[R_m]^2
        AVG(spy_return * spy_return) - (AVG(spy_return) * AVG(spy_return)) AS var_spy,
        -- StdDevs for Correlation
        SQRT(AVG(asset_return * asset_return) - (AVG(asset_return) * AVG(asset_return))) AS std_asset,
        SQRT(AVG(spy_return * spy_return) - (AVG(spy_return) * AVG(spy_return))) AS std_spy
    FROM asset_joined
    GROUP BY symbol, asset_name, sector
)
SELECT
    symbol,
    asset_name,
    sector,
    ROUND(cov_asset_spy / NULLIF(var_spy, 0), 2) AS market_beta,
    ROUND(cov_asset_spy / NULLIF(std_asset * std_spy, 0), 2) AS correlation_with_spy,
    CASE
        WHEN symbol = 'SPY' THEN 'Market Benchmark (Beta = 1.0)'
        WHEN cov_asset_spy / NULLIF(var_spy, 0) > 1.2 THEN 'Aggressive High Beta (> 1.2)'
        WHEN cov_asset_spy / NULLIF(var_spy, 0) BETWEEN 0.8 AND 1.2 THEN 'Core Market Correlated'
        WHEN cov_asset_spy / NULLIF(var_spy, 0) < 0.8 AND cov_asset_spy / NULLIF(var_spy, 0) >= 0 THEN 'Low Beta Defensive'
        ELSE 'Negative / Inverse Correlated'
    END AS beta_profile
FROM beta_calc
ORDER BY market_beta DESC;
