-- ==============================================================================
-- Query 02: Monthly Asset Returns Matrix
-- Purpose: Resamples daily market facts into monthly calendar returns.
-- Grain: One row per asset per calendar month
-- ==============================================================================

WITH monthly_asset_prices AS (
    SELECT
        a.symbol,
        d.calendar_year,
        d.calendar_month,
        MIN(d.calendar_date) AS month_start_date,
        MAX(d.calendar_date) AS month_end_date,
        -- First close of month
        (
            SELECT f_sub.adjusted_close
            FROM fact_market_daily f_sub
            JOIN dim_date d_sub ON f_sub.market_date_key = d_sub.date_key
            WHERE f_sub.asset_key = a.asset_key
              AND d_sub.calendar_year = d.calendar_year
              AND d_sub.calendar_month = d.calendar_month
            ORDER BY d_sub.calendar_date ASC
            LIMIT 1
        ) AS month_open_price,
        -- Last close of month
        (
            SELECT f_sub.adjusted_close
            FROM fact_market_daily f_sub
            JOIN dim_date d_sub ON f_sub.market_date_key = d_sub.date_key
            WHERE f_sub.asset_key = a.asset_key
              AND d_sub.calendar_year = d.calendar_year
              AND d_sub.calendar_month = d.calendar_month
            ORDER BY d_sub.calendar_date DESC
            LIMIT 1
        ) AS month_close_price
    FROM dim_asset a
    JOIN fact_market_daily f ON a.asset_key = f.asset_key
    JOIN dim_date d ON f.market_date_key = d.date_key
    GROUP BY a.asset_key, a.symbol, d.calendar_year, d.calendar_month
)
SELECT
    symbol,
    calendar_year,
    calendar_month,
    (CAST(calendar_year AS VARCHAR) || '-' || (CASE WHEN calendar_month < 10 THEN '0' || CAST(calendar_month AS VARCHAR) ELSE CAST(calendar_month AS VARCHAR) END)) AS year_month,
    ROUND(month_open_price, 2) AS month_open_price,
    ROUND(month_close_price, 2) AS month_close_price,
    ROUND(((month_close_price - month_open_price) / month_open_price) * 100.0, 2) AS monthly_return_pct
FROM monthly_asset_prices
ORDER BY symbol ASC, calendar_year DESC, calendar_month DESC;
