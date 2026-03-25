CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.mart_kpi_daily_operations AS
SELECT
    flight_date,
    COUNT(*) AS total_flights,
    ROUND(AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END), 4) AS on_time_rate,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY arr_delay_minutes), 2) AS p50_arr_delay_minutes,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY arr_delay_minutes), 2) AS p90_arr_delay_minutes,
    ROUND(AVG(CASE WHEN cancelled THEN 1.0 ELSE 0.0 END), 4) AS cancellation_rate,
    ROUND(AVG(CASE WHEN is_severe_delay THEN 1.0 ELSE 0.0 END), 4) AS severe_delay_rate,
    ROUND(100 * AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END), 2) AS reliability_score,
    ROUND(COALESCE(STDDEV_SAMP(arr_delay_minutes), 0), 2) AS volatility_index
FROM analytics.fct_flight_operations
GROUP BY 1
ORDER BY 1;
