CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.fct_trade_monthly AS
SELECT
    trade_id,
    period,
    reporter_iso,
    partner_iso,
    commodity_code,
    trade_flow,
    trade_value_usd,
    net_weight_kg,
    extracted_at
FROM bronze.comtrade_monthly;
