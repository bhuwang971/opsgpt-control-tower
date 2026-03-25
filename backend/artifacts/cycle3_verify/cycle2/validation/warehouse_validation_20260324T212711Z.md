# Cycle 2 Warehouse Validation

Generated at: `20260324T212711Z`

- `pass` analytics.dim_airport row_count: row_count=6
- `pass` analytics.dim_carrier row_count: row_count=3
- `pass` analytics.fct_flight_operations row_count: row_count=3
- `pass` analytics.mart_kpi_daily_operations row_count: row_count=2
- `pass` analytics.dim_airport.airport_code unique_not_null: null_count=0 duplicate_count=0
- `pass` analytics.dim_carrier.carrier_code unique_not_null: null_count=0 duplicate_count=0
- `pass` daily mart total flights reconcile to fact table: left=3 right=3
- `pass` carrier mart row count matches carrier grain: left=3 right=3
- `pass` fixture daily KPI 2024-01-05: actual=(2, 0.5, 0.0)
- `pass` fixture daily KPI 2024-01-06: actual=(1, 0.0, 1.0)
- `pass` fixture carrier KPI DL: actual=(1, 1.0)
