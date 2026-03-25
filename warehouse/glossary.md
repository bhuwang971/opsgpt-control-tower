# Warehouse Glossary

## Dimensions
- `analytics.dim_date`: canonical date grain used across operations and trade marts.
- `analytics.dim_airport`: airport codes found in flight data, enriched with primary weather-station coverage when available.
- `analytics.dim_carrier`: airline carrier dimension with coverage dates and total flight volume.
- `analytics.dim_trade_partner`: trade partner dimension with shipment counts and total trade value.
- `analytics.dim_commodity`: commodity dimension keyed by `commodity_code`.

## Facts
- `analytics.fct_flight_operations`: one row per flight with derived on-time and severe-delay flags.
- `analytics.fct_weather_observations`: one row per weather station observation with airport-code normalization.
- `analytics.fct_trade_monthly`: one row per trade record at monthly grain.

## KPI Marts
- `analytics.mart_kpi_daily_operations`: daily flight KPIs including on-time rate, delay percentiles, cancellation rate, reliability score, and volatility index.
- `analytics.mart_kpi_carrier_performance`: carrier-level operational KPI rollup.
- `analytics.mart_kpi_trade_monthly`: monthly trade KPI rollup by reporter and flow.

## KPI Definitions
- `on_time_rate`: share of non-cancelled flights with `arr_delay_minutes <= 15`.
- `cancellation_rate`: share of flights marked `cancelled = true`.
- `severe_delay_rate`: share of non-cancelled flights with `arr_delay_minutes >= 60`.
- `reliability_score`: `100 * on_time_rate`.
- `volatility_index`: sample standard deviation of `arr_delay_minutes` within the mart grain.
