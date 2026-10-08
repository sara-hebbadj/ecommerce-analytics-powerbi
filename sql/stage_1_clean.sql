-- Stage 1: clean, typed copies of the raw Olist tables (raw_* -> clean_*).
--
-- Rules used in this file (each one is counted in outputs/dq_log.csv by quality.py):
--   * Every raw column arrived as text. We cast with TRY_CAST: a bad value becomes NULL
--     instead of crashing the load, and the data-quality log counts those NULLs.
--   * Exact duplicate rows are removed. When a key is duplicated, we keep one row
--     with QUALIFY ROW_NUMBER() OVER (PARTITION BY key ...) = 1.
--   * Blank text is treated as missing: NULLIF(TRIM(x), '').
--   * Money is DECIMAL(12, 2), never floating point, so totals add up to the cent.


-- Customers. NOTE: Olist creates a new customer_id for EVERY order.
-- The real person is customer_unique_id (used for repeat customers and cohorts).
CREATE OR REPLACE TABLE clean_customers AS
SELECT
    customer_id,
    customer_unique_id,
    LPAD(TRIM(customer_zip_code_prefix), 5, '0') AS customer_zip_code_prefix,  -- keep leading zeros
    LOWER(TRIM(customer_city)) AS customer_city,
    UPPER(TRIM(customer_state)) AS customer_state
FROM raw_customers
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY customer_unique_id) = 1;


CREATE OR REPLACE TABLE clean_sellers AS
SELECT
    seller_id,
    LPAD(TRIM(seller_zip_code_prefix), 5, '0') AS seller_zip_code_prefix,
    LOWER(TRIM(seller_city)) AS seller_city,
    UPPER(TRIM(seller_state)) AS seller_state
FROM raw_sellers
QUALIFY ROW_NUMBER() OVER (PARTITION BY seller_id ORDER BY seller_state) = 1;


-- Products with an English category name.
CREATE OR REPLACE TABLE clean_products AS
WITH translation AS (
    -- One English name per Portuguese name, so the join below can never duplicate products.
    SELECT
        NULLIF(TRIM(product_category_name), '') AS category_pt,
        MIN(NULLIF(TRIM(product_category_name_english), '')) AS category_en
    FROM raw_category_translation
    GROUP BY 1
)
SELECT
    p.product_id,
    COALESCE(NULLIF(TRIM(p.product_category_name), ''), 'unknown') AS category_pt,
    -- English name; falls back to the Portuguese name when no translation exists.
    COALESCE(t.category_en, NULLIF(TRIM(p.product_category_name), ''), 'unknown') AS category,
    TRY_CAST(p.product_name_length AS INTEGER) AS name_length,
    TRY_CAST(p.product_description_length AS INTEGER) AS description_length,
    TRY_CAST(p.product_photos_qty AS INTEGER) AS photos_qty,
    TRY_CAST(p.product_weight_g AS DOUBLE) AS weight_g,
    TRY_CAST(p.product_length_cm AS DOUBLE) AS length_cm,
    TRY_CAST(p.product_height_cm AS DOUBLE) AS height_cm,
    TRY_CAST(p.product_width_cm AS DOUBLE) AS width_cm
FROM raw_products AS p
LEFT JOIN translation AS t
    ON t.category_pt = NULLIF(TRIM(p.product_category_name), '')
QUALIFY ROW_NUMBER() OVER (PARTITION BY p.product_id ORDER BY p.product_category_name) = 1;


-- Orders with typed dates and the flags every metric relies on.
CREATE OR REPLACE TABLE clean_orders AS
WITH typed AS (
    SELECT
        order_id,
        customer_id,
        LOWER(TRIM(order_status)) AS order_status,
        TRY_CAST(order_purchase_timestamp AS TIMESTAMP) AS purchase_ts,
        TRY_CAST(order_approved_at AS TIMESTAMP) AS approved_ts,
        TRY_CAST(order_delivered_carrier_date AS TIMESTAMP) AS carrier_ts,
        TRY_CAST(order_delivered_customer_date AS TIMESTAMP) AS delivered_ts,
        TRY_CAST(order_estimated_delivery_date AS TIMESTAMP) AS estimated_ts
    FROM raw_orders
    -- One row per order_id (duplicates are counted in the data-quality log).
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_purchase_timestamp) = 1
),
flagged AS (
    SELECT
        *,
        order_status = 'delivered' AS is_delivered,
        order_status IN ('canceled', 'unavailable') AS is_cancelled,
        -- Delivery-time metrics need both dates, and delivery cannot be before purchase.
        COALESCE(
            order_status = 'delivered'
            AND delivered_ts IS NOT NULL
            AND estimated_ts IS NOT NULL
            AND purchase_ts IS NOT NULL
            AND delivered_ts >= purchase_ts,
            FALSE
        ) AS has_valid_delivery
    FROM typed
)
SELECT
    *,
    CASE WHEN has_valid_delivery
        THEN DATE_DIFF('day', CAST(purchase_ts AS DATE), CAST(delivered_ts AS DATE))
    END AS delivery_days,
    -- Days late: positive = late, 0 = arrived on the promised day, negative = early.
    -- We compare DATES, not timestamps: the estimate is a date (00:00:00), so a parcel
    -- delivered at 18:00 on the promised day counts as on time.
    CASE WHEN has_valid_delivery
        THEN DATE_DIFF('day', CAST(estimated_ts AS DATE), CAST(delivered_ts AS DATE))
    END AS delay_days
FROM flagged;


CREATE OR REPLACE TABLE clean_order_items AS
SELECT
    order_id,
    TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
    product_id,
    seller_id,
    TRY_CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_ts,
    TRY_CAST(price AS DECIMAL(12, 2)) AS price,
    TRY_CAST(freight_value AS DECIMAL(12, 2)) AS freight_value  -- freight is stored per item
FROM (SELECT DISTINCT * FROM raw_order_items)  -- drop exact duplicate rows
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id, order_item_id ORDER BY product_id) = 1;


CREATE OR REPLACE TABLE clean_payments AS
SELECT DISTINCT
    order_id,
    TRY_CAST(payment_sequential AS INTEGER) AS payment_sequential,
    LOWER(TRIM(payment_type)) AS payment_type,
    TRY_CAST(payment_installments AS INTEGER) AS payment_installments,
    TRY_CAST(payment_value AS DECIMAL(12, 2)) AS payment_value
FROM raw_payments;


-- Reviews: one row per order. Some orders have several reviews; we keep the latest.
-- The review TEXT is deliberately not carried forward: it is free text written by real
-- customers and no question here needs it.
CREATE OR REPLACE TABLE clean_reviews AS
WITH typed AS (
    SELECT
        order_id,
        review_id,
        TRY_CAST(review_score AS INTEGER) AS raw_score,
        TRY_CAST(review_creation_date AS TIMESTAMP) AS review_created_ts,
        TRY_CAST(review_answer_timestamp AS TIMESTAMP) AS review_answered_ts
    FROM raw_reviews
)
SELECT
    order_id,
    review_id,
    CASE WHEN raw_score BETWEEN 1 AND 5 THEN raw_score END AS review_score,
    review_created_ts,
    review_answered_ts
FROM typed
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY review_answered_ts DESC NULLS LAST, review_created_ts DESC NULLS LAST, review_id
) = 1;


-- One centre point per state for the Power BI map: the median of the zip-prefix points.
-- The geolocation file repeats points many times and has a few points outside Brazil,
-- so we keep only points inside a rough box around Brazil (islands included).
CREATE OR REPLACE TABLE clean_state_centroids AS
SELECT
    UPPER(TRIM(geolocation_state)) AS state_code,
    ROUND(MEDIAN(lat), 4) AS latitude,
    ROUND(MEDIAN(lng), 4) AS longitude
FROM (
    SELECT
        geolocation_state,
        TRY_CAST(geolocation_lat AS DOUBLE) AS lat,
        TRY_CAST(geolocation_lng AS DOUBLE) AS lng
    FROM raw_geolocation
)
WHERE lat BETWEEN -34 AND 6
  AND lng BETWEEN -74 AND -32
GROUP BY 1;
