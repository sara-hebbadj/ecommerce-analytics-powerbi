-- Question: Which seller-state -> customer-state routes have the highest late-delivery rate?
-- Definitions: delivered orders with valid dates. A route is counted once per order (an
-- order with two sellers in different states counts on both routes). Only routes with at
-- least params.min_route_orders orders are shown; top 15 by late rate.
WITH order_routes AS (
    SELECT DISTINCT order_id, seller_state, customer_state, is_late
    FROM fact_order_items
    WHERE has_valid_delivery = 1
)
SELECT
    seller_state || ' -> ' || customer_state AS route,
    seller_state,
    customer_state,
    COUNT(*) AS orders,
    COUNT(*) FILTER (WHERE is_late = 1) AS late_orders,
    ROUND(100.0 * AVG(is_late), 2) AS late_rate_pct
FROM order_routes
GROUP BY seller_state, customer_state
HAVING COUNT(*) >= (SELECT min_route_orders FROM params)
ORDER BY late_rate_pct DESC, orders DESC, route
LIMIT 15;
