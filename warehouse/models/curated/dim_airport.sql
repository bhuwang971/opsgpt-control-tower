CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.dim_airport AS
WITH flight_airports AS (
    SELECT origin AS airport_code FROM bronze.bts_flights
    UNION
    SELECT destination AS airport_code FROM bronze.bts_flights
),
weather_airports AS (
    SELECT
        station_id,
        CASE
            WHEN LENGTH(station_id) = 4 AND LEFT(station_id, 1) = 'K' THEN SUBSTR(station_id, 2, 3)
            ELSE station_id
        END AS airport_code
    FROM bronze.weather_observations
)
SELECT
    f.airport_code,
    MAX(w.station_id) AS primary_weather_station,
    CASE WHEN MAX(w.station_id) IS NULL THEN FALSE ELSE TRUE END AS has_weather_coverage
FROM flight_airports AS f
LEFT JOIN weather_airports AS w
    ON f.airport_code = w.airport_code
WHERE f.airport_code IS NOT NULL
GROUP BY 1
ORDER BY 1;
