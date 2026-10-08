-- Question: How big is the freight cost compared with the price of the goods, overall
-- and by category?
-- Definitions: delivered orders only; freight share = freight / item price. ROLLUP adds a
-- total row; GROUPING(category) = 1 marks that row, which we label 'ALL CATEGORIES'.
SELECT
    CASE WHEN GROUPING(category) = 1 THEN 'ALL CATEGORIES' ELSE category END AS category,
    COUNT(DISTINCT order_id) AS orders,
    SUM(price) AS revenue,
    SUM(freight_value) AS freight,
    ROUND(100.0 * SUM(freight_value) / NULLIF(SUM(price), 0), 2) AS freight_share_pct,
    CAST(
        GROUPING(category) = 1
        OR COUNT(DISTINCT order_id) >= (SELECT min_category_orders FROM params)
        AS INTEGER
    ) AS enough_orders
FROM fact_order_items
WHERE is_delivered = 1
GROUP BY ROLLUP (category)
ORDER BY GROUPING(category) DESC, freight_share_pct DESC, category;
