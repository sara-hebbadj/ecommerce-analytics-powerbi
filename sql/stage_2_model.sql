-- Stage 2: the analysis model (clean_* -> fact_* and dim_*).
--
-- Two fact tables at different grains share the same dimensions (a "star schema"):
--   fact_orders       one row per order        (delivery, reviews, order totals)
--   fact_order_items  one row per order item   (categories, sellers, freight)
--   fact_payments     one row per payment line (payment types)
-- Every SQL question and every Power BI table is built from these tables, so the SQL
-- answers and the dashboard totals come from the same numbers (see reconcile.py).
--
-- Rule used everywhere: aggregate a child table to ONE ROW PER ORDER before joining it.
-- Joining raw items and raw payments together would multiply rows ("join fan-out")
-- and silently inflate revenue.


CREATE OR REPLACE TABLE fact_orders AS
WITH items AS (
    SELECT
        order_id,
        COUNT(*) AS items_count,
        COUNT(DISTINCT product_id) AS distinct_products,
        COUNT(DISTINCT seller_id) AS sellers_count,
        SUM(price) AS item_revenue,
        SUM(freight_value) AS freight_value
    FROM clean_order_items
    GROUP BY order_id
),
payments AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value,
        ARG_MAX(payment_type, payment_value) AS main_payment_type  -- the type that paid most
    FROM clean_payments
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,          -- per-order ID: kept only to demonstrate the repeat-customer trap
    c.customer_unique_id,   -- the real customer
    c.customer_state,
    c.customer_city,
    o.order_status,
    CAST(o.purchase_ts AS DATE) AS purchase_date,
    CAST(DATE_TRUNC('month', o.purchase_ts) AS DATE) AS purchase_month,
    CAST(o.estimated_ts AS DATE) AS estimated_date,
    CAST(o.delivered_ts AS DATE) AS delivered_date,
    CAST(o.is_delivered AS INTEGER) AS is_delivered,
    CAST(o.is_cancelled AS INTEGER) AS is_cancelled,
    CAST(o.has_valid_delivery AS INTEGER) AS has_valid_delivery,
    -- 1 = late, 0 = on time or early, NULL = cannot tell (not delivered or bad dates).
    CASE WHEN o.has_valid_delivery THEN CAST(o.delay_days > 0 AS INTEGER) END AS is_late,
    o.delivery_days,
    o.delay_days,
    -- Lateness buckets (used by q11 and the Power BI "review vs lateness" chart).
    CASE
        WHEN NOT o.has_valid_delivery THEN NULL
        WHEN o.delay_days <= 0 THEN 'On time or early'
        WHEN o.delay_days <= 3 THEN '1-3 days late'
        WHEN o.delay_days <= 7 THEN '4-7 days late'
        WHEN o.delay_days <= 14 THEN '8-14 days late'
        ELSE '15+ days late'
    END AS delay_bucket,
    CASE
        WHEN NOT o.has_valid_delivery THEN NULL
        WHEN o.delay_days <= 0 THEN 1
        WHEN o.delay_days <= 3 THEN 2
        WHEN o.delay_days <= 7 THEN 3
        WHEN o.delay_days <= 14 THEN 4
        ELSE 5
    END AS delay_bucket_order,  -- sort key, so the buckets are not sorted alphabetically
    COALESCE(i.items_count, 0) AS items_count,
    COALESCE(i.distinct_products, 0) AS distinct_products,
    COALESCE(i.sellers_count, 0) AS sellers_count,
    COALESCE(i.item_revenue, 0) AS item_revenue,     -- product revenue, BRL, excludes freight
    COALESCE(i.freight_value, 0) AS freight_value,
    p.payment_value,
    p.main_payment_type,
    r.review_score,
    -- Olist emails the review survey when the parcel arrives OR when the promised date is
    -- due, so a late order's review is often ANSWERED BEFORE the parcel arrived.
    -- 1 = answered before delivery, 0 = at or after delivery, NULL = cannot tell.
    CASE WHEN o.has_valid_delivery AND r.review_answered_ts IS NOT NULL
        THEN CAST(r.review_answered_ts < o.delivered_ts AS INTEGER)
    END AS review_answered_before_delivery
FROM clean_orders AS o
LEFT JOIN clean_customers AS c USING (customer_id)
LEFT JOIN items AS i USING (order_id)
LEFT JOIN payments AS p USING (order_id)
LEFT JOIN clean_reviews AS r USING (order_id);


CREATE OR REPLACE TABLE fact_order_items AS
SELECT
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    COALESCE(p.category, 'unknown') AS category,
    s.seller_state,
    o.customer_unique_id,
    o.customer_state,
    o.purchase_date,
    o.purchase_month,
    o.is_delivered,
    o.has_valid_delivery,
    o.is_late,
    o.review_score,
    i.price,
    i.freight_value
FROM clean_order_items AS i
JOIN fact_orders AS o USING (order_id)   -- inner join: drops items whose order is unknown
LEFT JOIN clean_products AS p USING (product_id)
LEFT JOIN clean_sellers AS s USING (seller_id);


CREATE OR REPLACE TABLE fact_payments AS
SELECT
    pay.order_id,
    pay.payment_sequential,
    pay.payment_type,
    pay.payment_installments,
    pay.payment_value,
    o.purchase_date,
    o.purchase_month,
    o.is_delivered,
    o.customer_state
FROM clean_payments AS pay
JOIN fact_orders AS o USING (order_id);


-- One row per real customer (customer_unique_id).
-- Cohort = month of the customer's FIRST DELIVERED order.
CREATE OR REPLACE TABLE dim_customer AS
SELECT
    customer_unique_id,
    ARG_MIN(customer_state, purchase_date) AS customer_state,  -- state at the first order
    ARG_MIN(customer_city, purchase_date) AS customer_city,
    MIN(purchase_date) AS first_order_date,
    CAST(DATE_TRUNC('month', MIN(purchase_date) FILTER (WHERE is_delivered = 1)) AS DATE)
        AS cohort_month,
    COUNT(*) AS orders_placed,
    COUNT(*) FILTER (WHERE is_delivered = 1) AS delivered_orders,
    CAST(COUNT(*) FILTER (WHERE is_delivered = 1) >= 2 AS INTEGER) AS is_repeat_customer
FROM fact_orders
WHERE customer_unique_id IS NOT NULL
GROUP BY customer_unique_id;


CREATE OR REPLACE TABLE dim_product AS
SELECT
    product_id, category, category_pt, weight_g, photos_qty, length_cm, height_cm, width_cm
FROM clean_products;


CREATE OR REPLACE TABLE dim_seller AS
SELECT seller_id, seller_zip_code_prefix, seller_city, seller_state
FROM clean_sellers;


-- The 27 Brazilian states (26 states + Distrito Federal) with their region,
-- plus a map centre point computed from the geolocation file.
CREATE OR REPLACE TABLE dim_state AS
WITH states (state_code, state_name, region) AS (
    VALUES
        ('AC', 'Acre', 'North'), ('AL', 'Alagoas', 'Northeast'), ('AP', 'Amapá', 'North'),
        ('AM', 'Amazonas', 'North'), ('BA', 'Bahia', 'Northeast'), ('CE', 'Ceará', 'Northeast'),
        ('DF', 'Distrito Federal', 'Central-West'), ('ES', 'Espírito Santo', 'Southeast'),
        ('GO', 'Goiás', 'Central-West'), ('MA', 'Maranhão', 'Northeast'),
        ('MT', 'Mato Grosso', 'Central-West'), ('MS', 'Mato Grosso do Sul', 'Central-West'),
        ('MG', 'Minas Gerais', 'Southeast'), ('PA', 'Pará', 'North'),
        ('PB', 'Paraíba', 'Northeast'), ('PR', 'Paraná', 'South'),
        ('PE', 'Pernambuco', 'Northeast'), ('PI', 'Piauí', 'Northeast'),
        ('RJ', 'Rio de Janeiro', 'Southeast'), ('RN', 'Rio Grande do Norte', 'Northeast'),
        ('RS', 'Rio Grande do Sul', 'South'), ('RO', 'Rondônia', 'North'),
        ('RR', 'Roraima', 'North'), ('SC', 'Santa Catarina', 'South'),
        ('SP', 'São Paulo', 'Southeast'), ('SE', 'Sergipe', 'Northeast'),
        ('TO', 'Tocantins', 'North')
)
SELECT
    s.state_code,
    s.state_name,
    s.region,
    s.state_name || ', Brazil' AS map_location,  -- text Power BI's map can geocode
    g.latitude,
    g.longitude
FROM states AS s
LEFT JOIN clean_state_centroids AS g USING (state_code)
ORDER BY s.state_code;


-- Calendar table for Power BI time intelligence: whole years, one row per day.
CREATE OR REPLACE TABLE dim_date AS
WITH bounds AS (
    SELECT
        CAST(DATE_TRUNC('year', MIN(purchase_date)) AS TIMESTAMP) AS first_day,
        CAST(DATE_TRUNC('year', MAX(purchase_date)) AS TIMESTAMP)
            + INTERVAL 1 YEAR - INTERVAL 1 DAY AS last_day
    FROM fact_orders
),
days AS (
    SELECT CAST(UNNEST(GENERATE_SERIES(first_day, last_day, INTERVAL 1 DAY)) AS DATE) AS date
    FROM bounds
)
SELECT
    date,
    YEAR(date) AS year,
    QUARTER(date) AS quarter,
    MONTH(date) AS month_number,
    STRFTIME(date, '%b') AS month_name,
    STRFTIME(date, '%Y-%m') AS year_month,
    CAST(DATE_TRUNC('month', date) AS DATE) AS month_start,
    ISODOW(date) AS weekday_number,  -- 1 = Monday
    STRFTIME(date, '%a') AS weekday_name
FROM days
ORDER BY date;
