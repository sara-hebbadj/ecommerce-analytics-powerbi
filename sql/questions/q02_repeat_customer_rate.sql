-- Question: What share of customers came back and placed a second delivered order,
-- and how long did they take to come back?
-- Trap: Olist creates a new customer_id for EVERY order, so counting by customer_id says
-- nobody ever returns. The person is customer_unique_id. Both numbers are shown so the
-- difference is visible.
-- Second trap (found on the real data): some "repeat" customers placed all their orders on
-- the SAME DAY (a basket split into several orders). They did not come back. The last four
-- columns count them and give the repeat rate and timing for customers who returned on a
-- LATER day.
-- Window functions: ROW_NUMBER() numbers each person's orders; LEAD() finds the next order;
-- MIN() OVER gives each person's first purchase date on every row.
WITH per_person AS (
    SELECT
        customer_unique_id,
        COUNT(*) AS delivered_orders,
        COUNT(DISTINCT purchase_date) AS order_days
    FROM fact_orders
    WHERE is_delivered = 1 AND customer_unique_id IS NOT NULL
    GROUP BY customer_unique_id
),
per_customer_id AS (  -- the WRONG way, kept only for comparison
    SELECT customer_id, COUNT(*) AS delivered_orders
    FROM fact_orders
    WHERE is_delivered = 1
    GROUP BY customer_id
),
ordered AS (
    SELECT
        customer_unique_id,
        purchase_date,
        MIN(purchase_date) OVER (PARTITION BY customer_unique_id) AS first_date,
        ROW_NUMBER() OVER (
            PARTITION BY customer_unique_id ORDER BY purchase_date, order_id
        ) AS order_number,
        DATE_DIFF(
            'day',
            purchase_date,
            LEAD(purchase_date) OVER (
                PARTITION BY customer_unique_id ORDER BY purchase_date, order_id
            )
        ) AS days_to_next_order
    FROM fact_orders
    WHERE is_delivered = 1 AND customer_unique_id IS NOT NULL
),
later_day AS (  -- first order placed on a later day than the first purchase
    SELECT
        customer_unique_id,
        DATE_DIFF('day', MIN(first_date), MIN(purchase_date)) AS days_to_later_order
    FROM ordered
    WHERE purchase_date > first_date
    GROUP BY customer_unique_id
),
counts AS (
    SELECT
        COUNT(*) AS customers,
        COUNT(*) FILTER (WHERE delivered_orders >= 2) AS repeat_customers,
        SUM(delivered_orders) AS delivered_orders,
        COUNT(*) FILTER (WHERE delivered_orders >= 2 AND order_days = 1)
            AS repeat_customers_same_day_only,
        COUNT(*) FILTER (WHERE order_days >= 2) AS customers_back_on_later_day
    FROM per_person
)
SELECT
    customers,
    repeat_customers,
    ROUND(100.0 * repeat_customers / customers, 2) AS repeat_rate_pct,
    ROUND(delivered_orders / customers, 3) AS orders_per_customer,
    (SELECT MEDIAN(days_to_next_order) FROM ordered WHERE order_number = 1)
        AS median_days_first_to_second_order,
    (SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE delivered_orders >= 2) / COUNT(*), 2)
     FROM per_customer_id) AS repeat_rate_pct_if_counted_by_customer_id,
    repeat_customers_same_day_only,
    customers_back_on_later_day,
    ROUND(100.0 * customers_back_on_later_day / customers, 2) AS repeat_rate_pct_later_day,
    (SELECT MEDIAN(days_to_later_order) FROM later_day) AS median_days_to_later_day_order
FROM counts;
