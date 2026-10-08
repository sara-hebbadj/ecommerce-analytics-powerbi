-- Question: Does the review score fall further the later an order arrives?
-- Definitions: delivered orders with valid dates and a review, grouped by days late
-- (the delay_bucket column is defined once, in sql/stage_2_model.sql).
-- A steady fall across buckets ("dose-response") is stronger evidence than a single
-- late/on-time split, but it is still correlation, not proof of cause.
SELECT
    delay_bucket_order,
    delay_bucket,
    COUNT(*) AS orders_with_review,
    ROUND(AVG(review_score), 2) AS avg_review,
    ROUND(100.0 * AVG(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END), 2) AS low_review_pct
FROM fact_orders
WHERE has_valid_delivery = 1 AND review_score IS NOT NULL
GROUP BY delay_bucket_order, delay_bucket
ORDER BY delay_bucket_order;
