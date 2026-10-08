"""Metric edge cases with answers worked out BY HAND from the synthetic fixture.

See tests/fixtures/olist_synthetic/README.md for the row-by-row design. If one of these
fails after a SQL change, either the SQL or the definition changed: decide which, on purpose.
"""

from dataclasses import replace

import duckdb
import pytest

from olist_analytics.analysis import build_tables
from olist_analytics.config import FIXTURE_DIR, FIXTURE_PARAMS, QUESTIONS_DIR
from olist_analytics.load import load_raw_tables


def by(df, column):
    return df.set_index(column)


def test_monthly_orders_and_revenue(results):
    monthly = results["q01_monthly_orders_revenue"]
    assert list(monthly["orders_placed"]) == [3, 3, 4, 3]
    assert list(monthly["orders_delivered"]) == [3, 2, 3, 2]
    assert list(monthly["revenue_delivered"]) == [550, 260, 400, 760]
    # Window function LAG(): Feb vs Jan = (260 - 550) / 550
    assert monthly["revenue_mom_pct"].iloc[1] == pytest.approx(-52.73)
    assert monthly["is_partial_month"].sum() == 0


def test_repeat_rate_uses_the_real_customer(results):
    row = results["q02_repeat_customer_rate"].iloc[0]
    # 7 people with a delivered order (A..G); A, C and E have two. D's 2nd order was
    # cancelled and B's 2nd is still shipping, so they do NOT count.
    assert row["customers"] == 7
    assert row["repeat_customers"] == 3
    assert row["repeat_rate_pct"] == pytest.approx(42.86)
    assert row["repeat_rate_pct_if_counted_by_customer_id"] == 0  # the trap
    assert row["median_days_first_to_second_order"] == 36  # 28, 36, 71 days
    # No same-day "repeat" customers in the fixture: all three came back on a later day.
    assert row["repeat_customers_same_day_only"] == 0
    assert row["customers_back_on_later_day"] == 3
    assert row["repeat_rate_pct_later_day"] == pytest.approx(42.86)
    assert row["median_days_to_later_day_order"] == 36


def _db_with_extra_rows(*statements):
    """Fixture database with a few raw rows changed BEFORE cleaning (for one edge case)."""
    con = duckdb.connect()
    load_raw_tables(con, FIXTURE_DIR)
    for sql in statements:
        con.execute(sql)
    build_tables(con, FIXTURE_PARAMS)
    return con


def test_same_day_second_order_is_not_a_return():
    # Person F (o09, 2017-02-14) places a second delivered order o14 on the SAME day.
    con = _db_with_extra_rows(
        "INSERT INTO raw_customers VALUES ('c14', 'uniq_F', '40010', 'salvador', 'BA')",
        "INSERT INTO raw_orders VALUES ('o14', 'c14', 'delivered', '2017-02-14 15:00:00', "
        "'2017-02-14 16:00:00', NULL, '2017-02-20 10:00:00', '2017-03-01 00:00:00')",
    )
    row = con.execute((QUESTIONS_DIR / "q02_repeat_customer_rate.sql").read_text()).fetchdf()
    row = row.iloc[0]
    assert row["repeat_customers"] == 4  # A, C, E and now F
    assert row["repeat_customers_same_day_only"] == 1  # F
    assert row["median_days_first_to_second_order"] == 32  # 0, 28, 36, 71
    assert row["customers_back_on_later_day"] == 3  # still A, C, E
    assert row["median_days_to_later_day_order"] == 36  # F does not count


def test_late_rate_by_state(results):
    states = by(results["q04_late_delivery_by_state"], "customer_state")
    assert states["delivered_orders"].sum() == 8  # o09 and o12 have unusable dates
    assert states["late_orders"].sum() == 2  # o02 (3 days) and o04 (10 days)
    assert states.loc["MG", "late_rate_pct"] == 50.0
    assert states.loc["SP", "late_rate_pct"] == pytest.approx(33.33)
    assert "BA" not in states.index  # o09 is the only BA order and has no delivery date


def test_reviews_late_vs_on_time(results):
    reviews = by(results["q05_review_late_vs_on_time"], "delivery_group")
    assert reviews.loc["on_time", "orders_with_review"] == 6
    assert reviews.loc["on_time", "avg_review"] == 4.5  # 5, 4, 5, 4, 5 (latest), 4
    assert reviews.loc["late", "avg_review"] == 1.5  # 2 and 1
    assert reviews.loc["late", "low_review_pct"] == 100.0
    assert reviews.loc["on_time", "low_review_pct"] == 0.0
    # Every fixture review was answered after its parcel arrived.
    assert reviews["answered_before_delivery"].sum() == 0
    assert reviews.loc["late", "answered_after_delivery"] == 2
    assert reviews.loc["late", "avg_review_answered_after_delivery"] == 1.5


def test_review_answered_before_late_delivery_is_counted():
    # o04: promised 2017-02-05, delivered 2017-02-15 10:00. Move its review answer to
    # 2017-02-06, i.e. after the promised date but while the customer was still waiting.
    con = _db_with_extra_rows(
        "UPDATE raw_reviews SET review_creation_date = '2017-02-06 00:00:00', "
        "review_answer_timestamp = '2017-02-06 10:00:00' WHERE order_id = 'o04'"
    )
    sql = (QUESTIONS_DIR / "q05_review_late_vs_on_time.sql").read_text()
    reviews = by(con.execute(sql).fetchdf(), "delivery_group")
    assert reviews.loc["late", "answered_before_delivery"] == 1  # o04, of o02 and o04
    assert reviews.loc["late", "answered_before_delivery_pct"] == 50.0
    assert reviews.loc["late", "avg_review_answered_after_delivery"] == 2.0  # o02 only
    assert reviews.loc["on_time", "answered_before_delivery"] == 0


def test_review_by_delay_bucket(results):
    buckets = by(results["q11_review_by_delay_bucket"], "delay_bucket")
    assert buckets.loc["1-3 days late", "avg_review"] == 2.0
    assert buckets.loc["8-14 days late", "avg_review"] == 1.0


def test_top_categories_and_revenue_share(results):
    cats = by(results["q03_top_categories"], "category")
    assert cats.loc["furniture_decor", "revenue_rank"] == 1  # 300 + 260
    assert cats.loc["health_beauty", "revenue"] == 550
    assert cats.loc["health_beauty", "orders"] == 5  # o04 counted once
    assert cats.loc["health_beauty", "avg_review"] == 3.6  # 5, 4, 1, 5, 3
    assert cats["revenue_share_pct"].sum() == pytest.approx(100, abs=0.05)


def test_review_rank_only_for_categories_with_enough_orders(build_db):
    con = build_db(replace(FIXTURE_PARAMS, min_category_orders=2))
    df = con.execute((QUESTIONS_DIR / "q03_top_categories.sql").read_text()).fetchdf()
    ranked = df.dropna(subset=["review_rank"]).set_index("category")["review_rank"]
    # Categories with >= 2 delivered orders: health_beauty (5), furniture_decor (2) and
    # computers_accessories (2). pc_gamer and unknown (1 order each) get no review rank.
    assert ranked.to_dict() == {
        "health_beauty": 1,
        "furniture_decor": 2,
        "computers_accessories": 3,
    }


def test_freight_share(results):
    freight = by(results["q06_freight_share"], "category")
    assert freight.loc["ALL CATEGORIES", "revenue"] == 1970
    assert freight.loc["ALL CATEGORIES", "freight"] == 258
    assert freight.loc["ALL CATEGORIES", "freight_share_pct"] == pytest.approx(13.10)
    assert freight.loc["furniture_decor", "freight_share_pct"] == pytest.approx(19.64)


def test_cohort_retention(results):
    cohorts = results["q07_cohort_retention"]
    jan = cohorts[cohorts["cohort_month"].astype(str).str.startswith("2017-01")]
    jan = jan.set_index("months_since_first")
    assert jan.loc[0, "cohort_size"] == 3  # A, B, C
    assert jan.loc[0, "retention_pct"] == 100.0
    assert jan.loc[1, "active_customers"] == 1  # A in February
    assert jan.loc[3, "retention_pct"] == pytest.approx(33.33)  # C in April


def test_seller_ranking(results):
    sellers = by(results["q08_seller_ranking"], "seller_id")
    assert sellers.loc["s02", "revenue_rank"] == 1  # 240 + 40 + 500
    assert sellers.loc["s01", "orders"] == 6
    assert sellers.loc["s01", "late_rate_pct"] == 50.0  # 2 late of 4 with usable dates
    assert sellers.loc["s01", "worse_than_marketplace"] == 1
    assert sellers.loc["s02", "worse_than_marketplace"] == 0


def test_payment_types(results):
    pay = by(results["q09_payment_types"], "payment_type")
    assert pay.loc["credit_card", "orders_using_type"] == 6
    assert pay.loc["credit_card", "pct_of_orders"] == 60.0
    assert "not_defined" not in pay.index  # only on the cancelled order
    assert pay["pct_of_orders"].sum() > 100  # o04 paid with card + voucher


def test_basket_size(results):
    basket = results["q10_basket_size"].iloc[0]
    assert basket["delivered_orders"] == 10
    assert basket["avg_items_per_order"] == 1.3  # 13 items / 10 orders
    assert basket["avg_distinct_products"] == 1.1  # o06 = 3 units of one product
    assert basket["avg_order_value"] == 197.0
    assert basket["median_order_value"] == 160.0
    assert basket["multi_item_order_pct"] == 20.0


def test_worst_route(results):
    routes = results["q12_worst_routes"]
    assert routes.iloc[0]["route"] == "SP -> MG"
    assert routes.iloc[0]["late_rate_pct"] == 100.0


def test_every_question_file_has_a_question_header():
    files = sorted(QUESTIONS_DIR.glob("q*.sql"))
    assert len(files) == 12
    for path in files:
        text = path.read_text()
        assert text.startswith("-- Question:"), path.name
        assert "raw_" not in text, f"{path.name} must query the model, not raw tables"
