CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.fct_weather_observations AS
SELECT
    station_id,
    CASE
        WHEN LENGTH(station_id) = 4 AND LEFT(station_id, 1) = 'K' THEN SUBSTR(station_id, 2, 3)
        ELSE station_id
    END AS airport_code,
    observed_at,
    CAST(observed_at AS DATE) AS observation_date,
    temperature_c,
    wind_speed_kts,
    precip_mm,
    condition,
    extracted_at
FROM bronze.weather_observations;
