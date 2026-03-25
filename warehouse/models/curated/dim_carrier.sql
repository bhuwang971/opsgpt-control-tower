CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.dim_carrier AS
SELECT
    carrier AS carrier_code,
    COUNT(*) AS total_flights,
    MIN(flight_date) AS first_flight_date,
    MAX(flight_date) AS last_flight_date
FROM bronze.bts_flights
WHERE carrier IS NOT NULL
GROUP BY 1
ORDER BY 1;
