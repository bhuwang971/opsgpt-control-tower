CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.dim_date AS
WITH all_dates AS (
    SELECT flight_date AS date_day FROM bronze.bts_flights
    UNION
    SELECT CAST(observed_at AS DATE) AS date_day FROM bronze.weather_observations
    UNION
    SELECT period AS date_day FROM bronze.comtrade_monthly
)
SELECT
    date_day,
    EXTRACT(YEAR FROM date_day) AS year_number,
    EXTRACT(MONTH FROM date_day) AS month_number,
    EXTRACT(DAY FROM date_day) AS day_number,
    STRFTIME(date_day, '%Y-%m') AS year_month,
    STRFTIME(date_day, '%A') AS weekday_name
FROM all_dates
WHERE date_day IS NOT NULL
ORDER BY date_day;
