-- Question: What share of customers came back and placed a second delivered order,
-- and how long did they take to come back?
-- Trap: Olist creates a new customer_id for EVERY order, so counting by customer_id says
-- nobody ever returns. The person is customer_unique_id. Both numbers are shown so the
-- difference is visible.
-- Window functions: ROW_NUMBER() numbers each person's orders; LEAD() finds the next order.
WITH per_person AS (
    SELECT customer_unique_id, COUNT(*) AS delivered_orders
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
counts AS (
    SELECT
        COUNT(*) AS customers,
        COUNT(*) FILTER (WHERE delivered_orders >= 2) AS repeat_customers,
        SUM(delivered_orders) AS delivered_orders
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
     FROM per_customer_id) AS repeat_rate_pct_if_counted_by_customer_id
FROM counts;
