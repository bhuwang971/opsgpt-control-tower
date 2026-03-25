CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.fct_flight_operations AS
SELECT
    flight_id,
    flight_date,
    carrier AS carrier_code,
    origin AS origin_airport_code,
    destination AS destination_airport_code,
    dep_delay_minutes,
    arr_delay_minutes,
    cancelled,
    CASE WHEN cancelled THEN FALSE WHEN arr_delay_minutes <= 15 THEN TRUE ELSE FALSE END AS is_on_time,
    CASE WHEN cancelled THEN FALSE WHEN arr_delay_minutes >= 60 THEN TRUE ELSE FALSE END AS is_severe_delay,
    extracted_at
FROM bronze.bts_flights;
