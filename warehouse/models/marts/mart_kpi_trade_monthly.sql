CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.mart_kpi_trade_monthly AS
SELECT
    period,
    reporter_iso,
    trade_flow,
    COUNT(*) AS shipment_count,
    SUM(trade_value_usd) AS total_trade_value_usd,
    AVG(net_weight_kg) AS avg_net_weight_kg
FROM analytics.fct_trade_monthly
GROUP BY 1, 2, 3
ORDER BY period, reporter_iso, trade_flow;
