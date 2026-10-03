WITH prices AS (
    SELECT
        f.asset_key,
        a.symbol,
        d.calendar_year,
        d.calendar_month,
        f.adjusted_close,
        d.calendar_date
    FROM fact_market_daily f
    JOIN dim_asset a ON f.asset_key = a.asset_key
    JOIN dim_date d ON f.market_date_key = d.date_key
),
ranked_month AS (
    SELECT
        asset_key,
        symbol,
        calendar_year,
        calendar_month,
        adjusted_close,
        ROW_NUMBER() OVER (PARTITION BY asset_key, calendar_year, calendar_month ORDER BY calendar_date ASC) AS first_day_rn,
        ROW_NUMBER() OVER (PARTITION BY asset_key, calendar_year, calendar_month ORDER BY calendar_date DESC) AS last_day_rn
    FROM prices
),
monthly_summary AS (
    SELECT
        r_start.symbol,
        r_start.calendar_year,
        r_start.calendar_month,
        r_start.adjusted_close AS start_price,
        r_end.adjusted_close AS end_price
    FROM ranked_month r_start
    JOIN ranked_month r_end ON r_start.asset_key = r_end.asset_key
        AND r_start.calendar_year = r_end.calendar_year
        AND r_start.calendar_month = r_end.calendar_month
    WHERE r_start.first_day_rn = 1 AND r_end.last_day_rn = 1
)
SELECT
    symbol,
    calendar_year,
    calendar_month,
    ROUND(start_price, 2) AS start_price,
    ROUND(end_price, 2) AS end_price,
    ROUND(((end_price - start_price) / NULLIF(start_price, 0)) * 100.0, 2) AS monthly_return_pct
FROM monthly_summary
