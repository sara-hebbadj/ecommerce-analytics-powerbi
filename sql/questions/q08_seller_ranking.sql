-- Question: Which sellers bring the most revenue, and which of them give customers a
-- worse experience (more late deliveries and lower reviews than the marketplace average)?
-- Definitions: delivered orders only; sellers with at least params.min_seller_orders orders.
-- An order with two sellers counts for both, and its lateness/review is shared by both
-- (the data cannot tell which parcel was late).
WITH seller_orders AS (
    SELECT
        seller_id,
        order_id,
        SUM(price) AS revenue,
        MAX(is_late) AS is_late,
        MAX(review_score) AS review_score
    FROM fact_order_items
    WHERE is_delivered = 1
    GROUP BY seller_id, order_id
),
seller_stats AS (
    SELECT
        seller_id,
        COUNT(*) AS orders,
        SUM(revenue) AS revenue,
        AVG(is_late) AS late_rate,
        AVG(review_score) AS avg_review
    FROM seller_orders
    GROUP BY seller_id
),
marketplace AS (
    SELECT AVG(is_late) AS late_rate, AVG(review_score) AS avg_review FROM seller_orders
)
SELECT
    s.seller_id,
    d.seller_state,
    s.orders,
    s.revenue,
    RANK() OVER (ORDER BY s.revenue DESC) AS revenue_rank,
    ROUND(100.0 * s.late_rate, 2) AS late_rate_pct,
    ROUND(s.avg_review, 2) AS avg_review,
    CAST(s.late_rate > m.late_rate AND s.avg_review < m.avg_review AS INTEGER)
        AS worse_than_marketplace
FROM seller_stats AS s
CROSS JOIN marketplace AS m
LEFT JOIN dim_seller AS d USING (seller_id)
WHERE s.orders >= (SELECT min_seller_orders FROM params)
ORDER BY revenue_rank, s.seller_id;
