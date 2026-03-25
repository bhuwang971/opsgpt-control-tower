CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.mart_kpi_carrier_performance AS
SELECT
    carrier_code,
    COUNT(*) AS total_flights,
    ROUND(AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END), 4) AS on_time_rate,
    ROUND(AVG(arr_delay_minutes), 2) AS avg_arr_delay_minutes,
    ROUND(AVG(CASE WHEN is_severe_delay THEN 1.0 ELSE 0.0 END), 4) AS severe_delay_rate,
    ROUND(AVG(CASE WHEN cancelled THEN 1.0 ELSE 0.0 END), 4) AS cancellation_rate
FROM analytics.fct_flight_operations
GROUP BY 1
ORDER BY on_time_rate DESC, avg_arr_delay_minutes ASC, carrier_code ASC;
