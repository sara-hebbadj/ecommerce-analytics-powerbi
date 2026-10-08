-- Question: In which customer states do deliveries arrive later than the date promised
-- at checkout, and by how much?
-- Definitions: late = delivered on a DATE after the estimated delivery date. Only delivered
-- orders with valid dates (has_valid_delivery = 1) are counted. enough_orders marks states
-- with at least params.min_state_orders orders; only those are called "worst".
SELECT
    customer_state,
    COUNT(*) AS delivered_orders,
    COUNT(*) FILTER (WHERE is_late = 1) AS late_orders,
    ROUND(100.0 * AVG(is_late), 2) AS late_rate_pct,
    ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
    ROUND(AVG(delay_days) FILTER (WHERE is_late = 1), 1) AS avg_days_late_when_late,
    CAST(COUNT(*) >= (SELECT min_state_orders FROM params) AS INTEGER) AS enough_orders
FROM fact_orders
WHERE has_valid_delivery = 1
GROUP BY customer_state
ORDER BY late_rate_pct DESC, delivered_orders DESC, customer_state;
