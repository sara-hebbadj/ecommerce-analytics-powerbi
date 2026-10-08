-- Question: How many orders were placed and delivered each month, and how much product
-- revenue did the delivered orders bring in?
-- Definitions: revenue = sum of item prices (BRL) of DELIVERED orders, excluding freight.
-- Orders are counted in the month they were PURCHASED. A month with fewer than 10% of the
-- median month's orders is flagged as partial (usually the first or last months of the data).
-- Window function: LAG() looks at the previous month's revenue to compute growth.
WITH monthly AS (
    SELECT
        purchase_month,
        COUNT(*) AS orders_placed,
        COUNT(*) FILTER (WHERE is_delivered = 1) AS orders_delivered,
        COUNT(*) FILTER (WHERE is_cancelled = 1) AS orders_cancelled,
        SUM(CASE WHEN is_delivered = 1 THEN item_revenue ELSE 0 END) AS revenue_delivered
    FROM fact_orders
    WHERE purchase_month IS NOT NULL
    GROUP BY purchase_month
)
SELECT
    purchase_month,
    orders_placed,
    orders_delivered,
    orders_cancelled,
    revenue_delivered,
    ROUND(revenue_delivered / NULLIF(orders_delivered, 0), 2) AS avg_order_value,
    ROUND(
        100.0 * (revenue_delivered - LAG(revenue_delivered) OVER (ORDER BY purchase_month))
        / NULLIF(LAG(revenue_delivered) OVER (ORDER BY purchase_month), 0),
        2
    ) AS revenue_mom_pct,
    CAST(orders_placed < 0.1 * (SELECT MEDIAN(orders_placed) FROM monthly) AS INTEGER)
        AS is_partial_month
FROM monthly
ORDER BY purchase_month;
