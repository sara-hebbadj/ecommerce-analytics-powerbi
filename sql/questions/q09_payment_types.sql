-- Question: How do customers pay (credit card, boleto, voucher, debit card), and how many
-- instalments do they use?
-- Definitions: delivered orders only. One order can use several payment types (for example
-- a voucher plus a card), so pct_of_orders can add up to more than 100%.
WITH totals AS (
    SELECT COUNT(DISTINCT order_id) AS orders, SUM(payment_value) AS value
    FROM fact_payments
    WHERE is_delivered = 1
)
SELECT
    payment_type,
    COUNT(DISTINCT order_id) AS orders_using_type,
    ROUND(100.0 * COUNT(DISTINCT order_id) / (SELECT orders FROM totals), 2) AS pct_of_orders,
    SUM(payment_value) AS payment_value,
    ROUND(100.0 * SUM(payment_value) / (SELECT value FROM totals), 2) AS pct_of_value,
    ROUND(AVG(payment_installments), 2) AS avg_installments
FROM fact_payments
WHERE is_delivered = 1
GROUP BY payment_type
ORDER BY payment_value DESC, payment_type;
