-- Question: Which product categories bring the most revenue, and which get the best and
-- worst review scores?
-- Definitions: delivered orders only; revenue = item prices (BRL). An order with several
-- items in one category counts ONCE for that category's review score. Review ranks are
-- given only to categories with at least params.min_category_orders orders, because small
-- categories have noisy averages.
WITH category_sales AS (
    SELECT
        category,
        COUNT(DISTINCT order_id) AS orders,
        SUM(price) AS revenue
    FROM fact_order_items
    WHERE is_delivered = 1
    GROUP BY category
),
category_reviews AS (
    SELECT category, AVG(review_score) AS avg_review, COUNT(*) AS reviewed_orders
    FROM (
        SELECT DISTINCT category, order_id, review_score
        FROM fact_order_items
        WHERE is_delivered = 1 AND review_score IS NOT NULL
    )
    GROUP BY category
),
joined AS (
    SELECT
        s.category,
        s.orders,
        s.revenue,
        r.avg_review,
        COALESCE(r.reviewed_orders, 0) AS reviewed_orders,
        s.orders >= (SELECT min_category_orders FROM params) AS enough_orders
    FROM category_sales AS s
    LEFT JOIN category_reviews AS r USING (category)
)
SELECT
    category,
    orders,
    revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS revenue_share_pct,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank,
    ROUND(avg_review, 2) AS avg_review,
    reviewed_orders,
    -- Rank only inside the "enough orders" group; small categories get no review rank.
    CASE WHEN enough_orders THEN
        RANK() OVER (PARTITION BY enough_orders ORDER BY avg_review DESC NULLS LAST)
    END AS review_rank,
    CAST(enough_orders AS INTEGER) AS enough_orders
FROM joined
ORDER BY revenue_rank, category;
