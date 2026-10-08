"""Power BI export, reconciliation, charts and the memo."""

import pandas as pd
import pytest

from olist_analytics.charts import cohort_grid, last_full_month
from olist_analytics.export_powerbi import AGGREGATE_TABLES, MODEL_TABLES
from olist_analytics.memo import render_memo


def test_reconciliation_all_match(pipeline_outputs):
    rec = pipeline_outputs["reconciliation"]
    assert len(rec) == 7
    assert rec["matches"].all(), rec[~rec["matches"]]


def test_powerbi_files_exist_with_keys(pipeline_outputs):
    folder = pipeline_outputs["out_dir"] / "powerbi"
    for table in MODEL_TABLES + list(AGGREGATE_TABLES):
        assert (folder / f"{table}.csv").exists(), table
    orders = pd.read_csv(folder / "fact_orders.csv")
    assert orders["order_id"].is_unique  # one row per order: safe "one" side in Power BI
    dates = pd.read_csv(folder / "dim_date.csv")
    assert dates["date"].is_unique and len(dates) == 365  # the whole year 2017


def test_exports_contain_no_review_text(pipeline_outputs):
    folder = pipeline_outputs["out_dir"] / "powerbi"
    for path in folder.glob("*.csv"):
        header = path.read_text().splitlines()[0]
        assert "comment" not in header, path.name


def test_five_charts_are_drawn(pipeline_outputs):
    charts = pipeline_outputs["charts"]
    assert len(charts) == 5
    assert all(path.stat().st_size > 5_000 for path in charts)


def test_cohort_grid_blanks_months_after_the_last_full_month(results):
    monthly = results["q01_monthly_orders_revenue"].copy()
    assert last_full_month(monthly) == pd.Timestamp("2017-04-01")  # fixture: no partial month
    # Pretend April is a partial month (like Sep-Oct 2018 in the real data).
    monthly.loc[
        monthly["purchase_month"].astype(str).str.startswith("2017-04"), "is_partial_month"
    ] = 1
    grid = cohort_grid(results["q07_cohort_retention"], 1, last_full_month(monthly))
    jan = grid.loc[pd.Timestamp("2017-01-01")]
    assert jan[1] == pytest.approx(33.33) and jan[2] == 0.0  # Feb and Mar observed
    assert pd.isna(jan[3])  # April is not a full month: blank, not 0% (C's return is hidden)
    assert pd.Timestamp("2017-03-01") not in grid.index  # no observable month: dropped


def test_memo_numbers_come_from_the_results(pipeline_outputs):
    facts = pipeline_outputs["facts"]
    assert facts["late_rate_pct"] == "25.0%"  # 2 of 8
    assert facts["avg_review_late"] == "1.50"
    # Gap 4.50 - 1.50 = 3.00; SE = sqrt(0.3/6 + 0.5/2) = 0.548; 3.00 +/- 1.96 * 0.548
    assert (facts["review_gap"], facts["review_gap_ci_low"], facts["review_gap_ci_high"]) == (
        "3.00",
        "1.93",
        "4.07",
    )
    assert facts["repeat_rate_pct"] == "42.9%"  # 3 of 7
    assert facts["repeat_same_day_only"] == "0"
    assert facts["repeat_rate_later_day_pct"] == "42.9%"
    assert facts["median_days_to_later_order"] == "36"
    # Comparing timestamps would add o07 (18:00 on the promised day): (2 + 1) / 8
    assert facts["late_rate_pct_by_timestamp"] == "37.5%"
    assert facts["late_answered_before_delivery_pct"] == "0.0%"
    assert facts["avg_review_late_answered_after_delivery"] == "1.50"
    assert facts["month1_retention_pct"] == "28.6%"  # (1 + 0 + 1) / (3 + 1 + 3)
    assert facts["top3_categories"] == "furniture_decor, health_beauty, pc_gamer"
    # What-if 1: MG 1 - 0.25*2 = 0.5 and SP 1 - 0.25*3 = 0.25 -> 0.75 late orders ~ 1
    assert facts["worst_state_codes"] == "MG, SP"
    assert facts["late_orders_avoided"] == "1"
    # What-if 3: (110 - 560*258/1970) + (80 - 550*258/1970) = 44.6
    assert facts["freight_reduction"] == "45"


def test_memo_has_no_unfilled_placeholders(pipeline_outputs):
    memo = pipeline_outputs["memo_path"].read_text()
    assert "$" not in memo
    assert "SYNTHETIC TEST FIXTURE" in memo  # demo memos are clearly labelled
    assert memo.count("TODO (Sara)") == 4  # Sara writes the conclusions and recommendations


def test_memo_fails_loudly_when_a_number_is_missing(pipeline_outputs):
    facts = dict(pipeline_outputs["facts"])
    del facts["late_rate_pct"]
    with pytest.raises(KeyError):
        render_memo(facts)
