CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.dim_trade_partner AS
SELECT
    partner_iso,
    COUNT(*) AS shipment_count,
    SUM(trade_value_usd) AS total_trade_value_usd,
    MIN(period) AS first_period,
    MAX(period) AS last_period
FROM bronze.comtrade_monthly
WHERE partner_iso IS NOT NULL
GROUP BY 1
ORDER BY total_trade_value_usd DESC, partner_iso ASC;
