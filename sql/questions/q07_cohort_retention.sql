-- Question: Of the customers whose first delivered order was in a given month (a cohort),
-- what share bought again 1, 2, 3 ... months later?
-- Definitions: real customers (customer_unique_id), delivered orders only.
-- months_since_first = 0 is the first month itself, so its retention is always 100%.
-- Window function: MIN() OVER (PARTITION BY customer) gives each customer's cohort month
-- on every one of their orders, without a separate join.
WITH orders AS (
    SELECT
        customer_unique_id,
        purchase_month,
        MIN(purchase_month) OVER (PARTITION BY customer_unique_id) AS cohort_month
    FROM fact_orders
    WHERE is_delivered = 1 AND customer_unique_id IS NOT NULL
),
activity AS (
    SELECT
        cohort_month,
        DATE_DIFF('month', cohort_month, purchase_month) AS months_since_first,
        COUNT(DISTINCT customer_unique_id) AS active_customers
    FROM orders
    GROUP BY cohort_month, months_since_first
),
cohort_sizes AS (
    SELECT cohort_month, active_customers AS cohort_size
    FROM activity
    WHERE months_since_first = 0
)
SELECT
    a.cohort_month,
    s.cohort_size,
    a.months_since_first,
    a.active_customers,
    ROUND(100.0 * a.active_customers / s.cohort_size, 2) AS retention_pct
FROM activity AS a
JOIN cohort_sizes AS s USING (cohort_month)
ORDER BY a.cohort_month, a.months_since_first;
