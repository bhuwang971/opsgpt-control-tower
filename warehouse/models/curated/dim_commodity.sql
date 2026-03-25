CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.dim_commodity AS
SELECT
    commodity_code,
    COUNT(*) AS shipment_count,
    SUM(trade_value_usd) AS total_trade_value_usd,
    AVG(net_weight_kg) AS avg_net_weight_kg
FROM bronze.comtrade_monthly
WHERE commodity_code IS NOT NULL
GROUP BY 1
ORDER BY total_trade_value_usd DESC, commodity_code ASC;
