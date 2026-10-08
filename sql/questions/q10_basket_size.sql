-- Question: How big is a typical basket: how many items, how many different products,
-- and how much money per delivered order?
-- Definitions: delivered orders only; order value = item prices (BRL), excluding freight.
-- The median is shown next to the mean because a few large orders pull the mean up.
SELECT
    COUNT(*) AS delivered_orders,
    ROUND(AVG(items_count), 3) AS avg_items_per_order,
    ROUND(AVG(distinct_products), 3) AS avg_distinct_products,
    ROUND(AVG(item_revenue), 2) AS avg_order_value,
    ROUND(MEDIAN(item_revenue), 2) AS median_order_value,
    ROUND(100.0 * AVG(CASE WHEN items_count >= 2 THEN 1 ELSE 0 END), 2) AS multi_item_order_pct
FROM fact_orders
WHERE is_delivered = 1;
