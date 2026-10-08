"""Cleaning rules and the data-quality log, checked against rows designed into the fixture."""


def one(db, sql):
    return db.execute(sql).fetchone()[0]


def test_data_quality_log_counts(pipeline_outputs):
    counts = pipeline_outputs["dq_log"].set_index("check")["rows_affected"].to_dict()
    expected = {
        "orders_duplicate_order_id": 1,  # o03 twice
        "orders_cancelled_or_unavailable": 2,  # o05, o13
        "orders_still_in_progress": 1,  # o10 shipped
        "orders_delivered_but_no_delivery_date": 1,  # o09
        "orders_delivered_before_purchase": 1,  # o12
        "orders_not_delivered_but_have_delivery_date": 1,  # o05
        "orders_customer_not_found": 0,
        "items_exact_duplicate_rows": 1,  # o03 item twice
        "items_order_not_found": 1,  # o99
        "products_missing_category": 1,  # p04
        "products_category_without_english_name": 1,  # p05 pc_gamer
        "reviews_review_id_reused": 1,  # r06
        "reviews_extra_reviews_for_same_order": 1,  # o08
        "reviews_score_missing_or_out_of_range": 1,  # score 6
        "delivered_orders_without_review": 1,  # o12
        "payments_type_not_defined": 1,
        "payments_zero_value": 1,
        "delivered_orders_payment_differs_from_items_plus_freight": 1,  # o12
        "customers_zip_prefix_lost_leading_zero": 1,  # c01
        "geolocation_exact_duplicate_rows": 1,
        "geolocation_points_outside_brazil": 1,
    }
    for check, value in expected.items():
        assert counts[check] == value, check


def test_every_check_has_a_denominator_and_an_action(pipeline_outputs):
    log = pipeline_outputs["dq_log"]
    assert (log["table_rows"] > 0).all()
    assert log["action"].str.len().gt(0).all()


def test_duplicate_order_removed(db):
    assert one(db, "SELECT COUNT(*) FROM fact_orders") == 13
    assert one(db, "SELECT COUNT(*) FROM fact_orders WHERE order_id = 'o03'") == 1


def test_zip_prefix_keeps_leading_zero(db):
    zip_code = one(
        db, "SELECT customer_zip_code_prefix FROM clean_customers WHERE customer_id='c01'"
    )
    assert zip_code == "01310"


def test_cancelled_order_with_delivery_date_is_not_delivered(db):
    row = db.execute(
        "SELECT is_delivered, is_cancelled, is_late FROM fact_orders WHERE order_id = 'o05'"
    ).fetchone()
    assert row == (0, 1, None)


def test_same_day_delivery_counts_as_on_time(db):
    row = db.execute("SELECT delay_days, is_late FROM fact_orders WHERE order_id='o07'").fetchone()
    assert row == (0, 0)


def test_bad_delivery_dates_are_excluded_from_lateness(db):
    rows = db.execute(
        "SELECT order_id, has_valid_delivery, is_late FROM fact_orders "
        "WHERE order_id IN ('o09', 'o12') ORDER BY order_id"
    ).fetchall()
    assert rows == [("o09", 0, None), ("o12", 0, None)]


def test_latest_review_is_kept_and_bad_score_dropped(db):
    assert one(db, "SELECT review_score FROM fact_orders WHERE order_id = 'o08'") == 5
    assert one(db, "SELECT review_score FROM fact_orders WHERE order_id = 'o10'") is None


def test_category_fallbacks(db):
    rows = dict(db.execute("SELECT product_id, category FROM dim_product").fetchall())
    assert rows["p01"] == "health_beauty"
    assert rows["p04"] == "unknown"  # no category
    assert rows["p05"] == "pc_gamer"  # no English name: Portuguese kept


def test_orphan_item_is_not_in_the_model(db):
    assert one(db, "SELECT COUNT(*) FROM fact_order_items WHERE order_id = 'o99'") == 0


def test_money_is_exact_decimal(db):
    column_type = one(
        db,
        "SELECT data_type FROM information_schema.columns "
        "WHERE table_name = 'clean_order_items' AND column_name = 'price'",
    )
    assert column_type.startswith("DECIMAL")


def test_state_map_points_ignore_points_outside_brazil(db):
    sp = db.execute("SELECT latitude, longitude FROM dim_state WHERE state_code='SP'").fetchone()
    assert sp == (-23.56, -46.65)
    assert one(db, "SELECT COUNT(*) FROM dim_state") == 27
