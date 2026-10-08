"""Data-quality checks. Each check counts the rows a cleaning rule touched.

The result is outputs/dq_log.csv: one line per check with the number of rows affected,
the size of the table it was measured on, and what the pipeline did about it.
A count of 0 is a valid, useful result ("we looked and found none").
"""

from dataclasses import dataclass

import duckdb
import pandas as pd


@dataclass(frozen=True)
class Check:
    name: str
    table: str  # the table whose row count is the denominator
    count_sql: str  # SQL returning one number: rows affected
    action: str  # what the pipeline does with these rows


BRAZIL_BOX = "lat BETWEEN -34 AND 6 AND lng BETWEEN -74 AND -32"

CHECKS = [
    # --- Orders ---
    Check(
        "orders_duplicate_order_id",
        "raw_orders",
        "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM raw_orders",
        "Kept one row per order_id.",
    ),
    Check(
        "orders_unreadable_purchase_timestamp",
        "raw_orders",
        "SELECT COUNT(*) FROM raw_orders "
        "WHERE TRY_CAST(order_purchase_timestamp AS TIMESTAMP) IS NULL",
        "Kept; left out of monthly and cohort results (no month).",
    ),
    Check(
        "orders_cancelled_or_unavailable",
        "clean_orders",
        "SELECT COUNT(*) FROM clean_orders WHERE is_cancelled",
        "Excluded from revenue, repeat-customer and delivery metrics.",
    ),
    Check(
        "orders_still_in_progress",
        "clean_orders",
        "SELECT COUNT(*) FROM clean_orders WHERE NOT is_delivered AND NOT is_cancelled",
        "Not delivered yet: excluded from revenue and delivery metrics.",
    ),
    Check(
        "orders_delivered_but_no_delivery_date",
        "clean_orders",
        "SELECT COUNT(*) FROM clean_orders WHERE is_delivered AND delivered_ts IS NULL",
        "Counted in revenue; excluded from delivery-time and lateness metrics.",
    ),
    Check(
        "orders_delivered_before_purchase",
        "clean_orders",
        "SELECT COUNT(*) FROM clean_orders WHERE is_delivered AND delivered_ts < purchase_ts",
        "Counted in revenue; excluded from delivery-time and lateness metrics.",
    ),
    Check(
        "orders_on_time_by_date_but_late_by_timestamp",
        "clean_orders",
        "SELECT COUNT(*) FROM clean_orders "
        "WHERE has_valid_delivery AND delay_days = 0 AND delivered_ts > estimated_ts",
        "Counted as on time (late compares dates). Comparing timestamps instead would "
        "add these orders to the late count.",
    ),
    Check(
        "orders_not_delivered_but_have_delivery_date",
        "clean_orders",
        "SELECT COUNT(*) FROM clean_orders WHERE NOT is_delivered AND delivered_ts IS NOT NULL",
        "Status wins: treated as not delivered.",
    ),
    Check(
        "orders_customer_not_found",
        "clean_orders",
        "SELECT COUNT(*) FROM clean_orders AS o "
        "LEFT JOIN clean_customers AS c USING (customer_id) WHERE c.customer_id IS NULL",
        "Kept in sales totals; left out of customer metrics (no customer_unique_id).",
    ),
    Check(
        "delivered_orders_without_items",
        "fact_orders",
        "SELECT COUNT(*) FROM fact_orders WHERE is_delivered = 1 AND items_count = 0",
        "Kept; they add 0 revenue and slightly lower the average order value.",
    ),
    # --- Order items ---
    Check(
        "items_exact_duplicate_rows",
        "raw_order_items",
        "SELECT (SELECT COUNT(*) FROM raw_order_items) "
        "- (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM raw_order_items))",
        "Removed.",
    ),
    Check(
        "items_duplicate_order_item_key",
        "raw_order_items",
        "SELECT (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM raw_order_items)) "
        "- (SELECT COUNT(*) FROM clean_order_items)",
        "Kept one row per (order_id, order_item_id).",
    ),
    Check(
        "items_missing_or_non_positive_price",
        "clean_order_items",
        "SELECT COUNT(*) FROM clean_order_items WHERE price IS NULL OR price <= 0",
        "Kept; they add nothing to revenue. Review manually if the count is large.",
    ),
    Check(
        "items_order_not_found",
        "clean_order_items",
        "SELECT COUNT(*) FROM clean_order_items AS i "
        "LEFT JOIN clean_orders AS o USING (order_id) WHERE o.order_id IS NULL",
        "Dropped from the model (no order to attach them to).",
    ),
    # --- Products ---
    Check(
        "products_missing_category",
        "clean_products",
        "SELECT COUNT(*) FROM clean_products WHERE category_pt = 'unknown'",
        "Labelled 'unknown'.",
    ),
    Check(
        "products_category_without_english_name",
        "clean_products",
        # Uses the explicit flag: several real names are identical in both languages
        # (e.g. 'pet_shop'), so comparing the two names over-counts (see README section 6).
        "SELECT COUNT(*) FROM clean_products "
        "WHERE category_pt <> 'unknown' AND NOT has_english_name",
        "Portuguese category name used instead.",
    ),
    # --- Reviews ---
    Check(
        "reviews_review_id_reused",
        "raw_reviews",
        "SELECT COUNT(*) - COUNT(DISTINCT review_id) FROM raw_reviews",
        "Information only: reviews are matched to orders by order_id, not review_id.",
    ),
    Check(
        "reviews_extra_reviews_for_same_order",
        "raw_reviews",
        "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM raw_reviews",
        "Kept only the latest review for each order.",
    ),
    Check(
        "reviews_score_missing_or_out_of_range",
        "raw_reviews",
        "SELECT COUNT(*) FROM raw_reviews "
        "WHERE COALESCE(TRY_CAST(review_score AS INTEGER) NOT BETWEEN 1 AND 5, TRUE)",
        "Score set to missing.",
    ),
    Check(
        "delivered_orders_without_review",
        "fact_orders",
        "SELECT COUNT(*) FROM fact_orders WHERE is_delivered = 1 AND review_score IS NULL",
        "Left out of review metrics.",
    ),
    # --- Payments ---
    Check(
        "payments_type_not_defined",
        "clean_payments",
        "SELECT COUNT(*) FROM clean_payments WHERE payment_type = 'not_defined'",
        "Kept as its own payment type.",
    ),
    Check(
        "payments_zero_value",
        "clean_payments",
        "SELECT COUNT(*) FROM clean_payments WHERE payment_value = 0",
        "Kept.",
    ),
    Check(
        "delivered_orders_payment_differs_from_items_plus_freight",
        "fact_orders",
        "SELECT COUNT(*) FROM fact_orders WHERE is_delivered = 1 "
        "AND ABS(COALESCE(payment_value, 0) - (item_revenue + freight_value)) > 1",
        "Information only: revenue uses item prices, not payments "
        "(vouchers and instalment interest can make them differ).",
    ),
    # --- Customers, sellers, geolocation ---
    Check(
        "customers_zip_prefix_lost_leading_zero",
        "raw_customers",
        "SELECT COUNT(*) FROM raw_customers WHERE LENGTH(TRIM(customer_zip_code_prefix)) < 5",
        "Left-padded with zeros to 5 digits.",
    ),
    Check(
        "sellers_zip_prefix_lost_leading_zero",
        "raw_sellers",
        "SELECT COUNT(*) FROM raw_sellers WHERE LENGTH(TRIM(seller_zip_code_prefix)) < 5",
        "Left-padded with zeros to 5 digits.",
    ),
    Check(
        "geolocation_exact_duplicate_rows",
        "raw_geolocation",
        "SELECT (SELECT COUNT(*) FROM raw_geolocation) "
        "- (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM raw_geolocation))",
        "Harmless: only one median point per state is used.",
    ),
    Check(
        "geolocation_points_outside_brazil",
        "raw_geolocation",
        "SELECT COUNT(*) FROM (SELECT TRY_CAST(geolocation_lat AS DOUBLE) AS lat, "
        "TRY_CAST(geolocation_lng AS DOUBLE) AS lng FROM raw_geolocation) "
        f"WHERE NOT COALESCE({BRAZIL_BOX}, FALSE)",
        "Ignored when computing the state map points.",
    ),
]


def run_quality_checks(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Run every check and return the data-quality log as a table."""
    rows = []
    for check in CHECKS:
        affected = con.execute(check.count_sql).fetchone()[0]
        total = con.execute(f"SELECT COUNT(*) FROM {check.table}").fetchone()[0]
        rows.append(
            {
                "check": check.name,
                "table": check.table,
                "rows_affected": int(affected),
                "table_rows": int(total),
                "pct_of_table": round(100.0 * affected / total, 3) if total else 0.0,
                "action": check.action,
            }
        )
    return pd.DataFrame(rows)
