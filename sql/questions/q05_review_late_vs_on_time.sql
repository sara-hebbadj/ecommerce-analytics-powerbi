-- Question: Do late orders get worse review scores than on-time orders?
-- Definitions: delivered orders with valid dates AND a review. Low review = 1 or 2 stars.
-- This shows an association (correlation), not proof that lateness causes bad reviews.
-- The confidence interval in the memo covers sampling noise only, not other causes.
SELECT
    CASE WHEN is_late = 1 THEN 'late' ELSE 'on_time' END AS delivery_group,
    COUNT(*) AS orders_with_review,
    ROUND(AVG(review_score), 2) AS avg_review,
    -- Standard deviation: used by memo.py for a 95% confidence interval of the gap.
    ROUND(STDDEV_SAMP(review_score), 4) AS sd_review,
    ROUND(100.0 * AVG(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END), 2) AS low_review_pct,
    ROUND(100.0 * AVG(CASE WHEN review_score = 5 THEN 1 ELSE 0 END), 2) AS five_star_pct,
    -- Review ANSWERED before the parcel arrived: the customer was still waiting, so the
    -- score may rate "not arrived yet" rather than "arrived late" (found on the real data).
    COUNT(*) FILTER (WHERE review_answered_before_delivery = 1) AS answered_before_delivery,
    ROUND(100.0 * AVG(CASE WHEN review_answered_before_delivery = 1 THEN 1 ELSE 0 END), 2)
        AS answered_before_delivery_pct,
    -- Average score of the reviews answered at or after delivery (the parcel had arrived).
    COUNT(*) FILTER (WHERE review_answered_before_delivery = 0) AS answered_after_delivery,
    ROUND(AVG(review_score) FILTER (WHERE review_answered_before_delivery = 0), 2)
        AS avg_review_answered_after_delivery
FROM fact_orders
WHERE has_valid_delivery = 1 AND review_score IS NOT NULL
GROUP BY delivery_group
ORDER BY delivery_group DESC;  -- on_time first
