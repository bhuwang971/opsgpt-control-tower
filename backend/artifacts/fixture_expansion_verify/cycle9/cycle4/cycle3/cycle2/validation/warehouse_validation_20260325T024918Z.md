# Cycle 2 Warehouse Validation

Generated at: `20260325T024918Z`

- `pass` analytics.dim_airport row_count: row_count=18
- `pass` analytics.dim_carrier row_count: row_count=4
- `pass` analytics.fct_flight_operations row_count: row_count=18
- `pass` analytics.mart_kpi_daily_operations row_count: row_count=6
- `pass` analytics.dim_airport.airport_code unique_not_null: null_count=0 duplicate_count=0
- `pass` analytics.dim_carrier.carrier_code unique_not_null: null_count=0 duplicate_count=0
- `pass` daily mart total flights reconcile to fact table: left=18 right=18
- `pass` carrier mart row count matches carrier grain: left=4 right=4
- `pass` fixture daily KPI 2024-01-05: actual=(3, 0.3333, 0.0)
- `pass` fixture daily KPI 2024-01-06: actual=(3, 0.3333, 0.3333)
- `pass` fixture carrier KPI DL: actual=(5, 0.2)
