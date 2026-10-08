"""Fill the one-page memo template with numbers computed from the SQL results.

Two steps, kept separate so each can be tested:
1. build_facts(): read the results tables and compute every number the memo needs.
   Each value is already formatted as text ("12.3%", "1,234").
2. render_memo(): put those values into memo/MEMO_TEMPLATE.md. string.Template raises
   an error if any $placeholder has no value, so a number can never be silently missing.
"""

import json
import math
from datetime import date
from pathlib import Path
from string import Template

import pandas as pd

from olist_analytics.config import MEMO_TEMPLATE, Params


# --- Formatting helpers: one place decides how numbers look in the memo ---
def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def fmt_int(value: float) -> str:
    return f"{round(value):,}"


def fmt_money(value: float) -> str:
    return f"{value:,.0f}"


def fmt_stars(value: float) -> str:
    return f"{value:.2f}"


def fmt_month(value) -> str:
    return pd.Timestamp(value).strftime("%b %Y")


def _list_or_none(items: list[str]) -> str:
    return ", ".join(items) if items else "none with enough orders"


def _days_or_na(value) -> str:
    return fmt_int(value) if pd.notna(value) else "n/a"


# --- Finding 1: lateness and reviews ---
def review_gap_ci(reviews: pd.DataFrame) -> tuple[float, float, float]:
    """On-time minus late average review, with a 95% confidence interval.

    Normal approximation for a difference of two means: gap +/- 1.96 * standard error,
    where SE = sqrt(sd1^2 / n1 + sd2^2 / n2). It measures sampling noise only: it cannot
    tell whether lateness CAUSES lower reviews.
    """
    if "late" not in reviews.index:
        return float("nan"), float("nan"), float("nan")
    on_time, late = reviews.loc["on_time"], reviews.loc["late"]
    gap = on_time["avg_review"] - late["avg_review"]
    se = math.sqrt(
        on_time["sd_review"] ** 2 / on_time["orders_with_review"]
        + late["sd_review"] ** 2 / late["orders_with_review"]
    )
    return gap, gap - 1.96 * se, gap + 1.96 * se


def review_by_bucket(buckets: pd.DataFrame) -> str:
    """One line per lateness bucket: 'On time or early 4.29 (n=...); 1-3 days late ...'."""
    return "; ".join(
        f"{r.delay_bucket} {fmt_stars(r.avg_review)} (n={fmt_int(r.orders_with_review)})"
        for r in buckets.sort_values("delay_bucket_order").itertuples()
    )


def late_rate_by_timestamp(results: dict[str, pd.DataFrame], dq_log: pd.DataFrame) -> str:
    """Sensitivity check: the late rate if timestamps were compared instead of dates."""
    states = results["q04_late_delivery_by_state"]
    extra = dq_log.set_index("check").loc[
        "orders_on_time_by_date_but_late_by_timestamp", "rows_affected"
    ]
    return fmt_pct(100 * (states["late_orders"].sum() + extra) / states["delivered_orders"].sum())


def delivery_facts(results: dict[str, pd.DataFrame], params: Params) -> dict:
    states = results["q04_late_delivery_by_state"]
    reviews = results["q05_review_late_vs_on_time"].set_index("delivery_group")
    national_rate = states["late_orders"].sum() / states["delivered_orders"].sum()

    eligible = states[states["enough_orders"] == 1].sort_values(
        ["late_rate_pct", "delivered_orders"], ascending=[False, False]
    )
    worst_three = eligible.head(3)
    what_if_states = eligible.head(params.worst_states_for_what_if)
    what_if_states = what_if_states[what_if_states["late_rate_pct"] / 100 > national_rate]

    # What-if: if these states had the national late rate, how many late orders fewer?
    late_avoided = (
        what_if_states["late_orders"] - national_rate * what_if_states["delivered_orders"]
    ).sum()
    low_late = reviews.loc["late", "low_review_pct"] if "late" in reviews.index else 0.0
    low_on_time = reviews.loc["on_time", "low_review_pct"]
    # ...and if those orders then got on-time-like reviews, how many 1-2 star reviews fewer?
    low_reviews_avoided = late_avoided * (low_late - low_on_time) / 100

    has_late = "late" in reviews.index
    avg_late = reviews.loc["late", "avg_review"] if has_late else float("nan")
    # Reviews answered before the parcel arrived, and the score of those answered after it.
    late_before = reviews.loc["late", "answered_before_delivery_pct"] if has_late else 0.0
    late_after_n = reviews.loc["late", "answered_after_delivery"] if has_late else 0
    late_after_avg = (
        reviews.loc["late", "avg_review_answered_after_delivery"] if has_late else float("nan")
    )
    gap, ci_low, ci_high = review_gap_ci(reviews)
    return {
        "review_gap": fmt_stars(gap),
        "review_gap_ci_low": fmt_stars(ci_low),
        "review_gap_ci_high": fmt_stars(ci_high),
        "late_rate_pct": fmt_pct(100 * national_rate),
        "avg_review_late": fmt_stars(avg_late),
        "avg_review_on_time": fmt_stars(reviews.loc["on_time", "avg_review"]),
        "low_review_pct_late": fmt_pct(low_late),
        "low_review_pct_on_time": fmt_pct(low_on_time),
        "late_answered_before_delivery_pct": fmt_pct(late_before),
        "late_answered_after_delivery": fmt_int(late_after_n),
        "avg_review_late_answered_after_delivery": fmt_stars(late_after_avg)
        if pd.notna(late_after_avg)
        else "n/a",
        "review_by_delay_buckets": review_by_bucket(results["q11_review_by_delay_bucket"]),
        "worst_states": _list_or_none(
            [f"{r.customer_state} ({fmt_pct(r.late_rate_pct)})" for r in worst_three.itertuples()]
        ),
        "worst_state_codes": _list_or_none(list(what_if_states["customer_state"])),
        "what_if_state_count": str(len(what_if_states)),
        "late_orders_avoided": fmt_int(late_avoided),
        "low_reviews_avoided": fmt_int(low_reviews_avoided),
    }


# --- Finding 2: repeat customers and cohorts ---
def customer_facts(results: dict[str, pd.DataFrame], aov: float) -> dict:
    repeat = results["q02_repeat_customer_rate"].iloc[0]
    monthly = results["q01_monthly_orders_revenue"]
    cohorts = results["q07_cohort_retention"]

    # Month-1 retention is only fair for cohorts whose following month is a FULL month.
    full_months = pd.to_datetime(monthly.loc[monthly["is_partial_month"] == 0, "purchase_month"])
    last_full_month = full_months.max()
    cohort_month = pd.to_datetime(cohorts["cohort_month"])
    sizes = cohorts[(cohorts["months_since_first"] == 0) & (cohort_month < last_full_month)]
    month1 = cohorts[(cohorts["months_since_first"] == 1) & (cohort_month < last_full_month)]
    month1_rate = 100 * month1["active_customers"].sum() / max(sizes["cohort_size"].sum(), 1)

    extra_repeat = repeat["customers"] * 0.01  # +1 percentage point of repeat rate
    same_day = repeat["repeat_customers_same_day_only"]
    return {
        "customers": fmt_int(repeat["customers"]),
        "repeat_customers": fmt_int(repeat["repeat_customers"]),
        "repeat_rate_pct": fmt_pct(repeat["repeat_rate_pct"]),
        "repeat_rate_by_customer_id": fmt_pct(repeat["repeat_rate_pct_if_counted_by_customer_id"]),
        "median_days_to_second_order": _days_or_na(repeat["median_days_first_to_second_order"]),
        # Same-day "repeat" customers split one basket into several orders; they did not return.
        "repeat_same_day_only": fmt_int(same_day),
        "repeat_same_day_only_pct": fmt_pct(100 * same_day / max(repeat["repeat_customers"], 1)),
        "repeat_rate_later_day_pct": fmt_pct(repeat["repeat_rate_pct_later_day"]),
        "median_days_to_later_order": _days_or_na(repeat["median_days_to_later_day_order"]),
        "month1_retention_pct": fmt_pct(month1_rate),
        "month1_cohorts": str(len(sizes)),
        "extra_repeat_customers_per_point": fmt_int(extra_repeat),
        "revenue_per_repeat_point": fmt_money(extra_repeat * aov),
    }


# --- Finding 3: categories and freight ---
def category_facts(results: dict[str, pd.DataFrame], params: Params) -> dict:
    # 'unknown' is a data-quality bucket, not a real category, so it is left out here.
    cats = results["q03_top_categories"]
    cats = cats[cats["category"] != "unknown"].sort_values("revenue", ascending=False)
    top3 = cats.head(3)

    freight = results["q06_freight_share"]
    overall = freight[freight["category"] == "ALL CATEGORIES"].iloc[0]
    overall_share = overall["freight"] / overall["revenue"]  # unrounded
    heavy = freight[
        (freight["category"] != "ALL CATEGORIES")
        & (freight["category"] != "unknown")
        & (freight["enough_orders"] == 1)
    ].sort_values("freight_share_pct", ascending=False)
    heavy = heavy.head(5)
    heavy = heavy[heavy["freight_share_pct"] / 100 > overall_share]
    # What-if: freight in these categories if their share fell to the overall share.
    freight_reduction = (heavy["freight"] - overall_share * heavy["revenue"]).sum()

    return {
        "top3_categories": _list_or_none(list(top3["category"])),
        "top3_revenue_share_pct": fmt_pct(top3["revenue_share_pct"].sum()),
        "freight_share_pct": fmt_pct(overall["freight_share_pct"]),
        "high_freight_categories": _list_or_none(
            [f"{r.category} ({fmt_pct(r.freight_share_pct)})" for r in heavy.itertuples()]
        ),
        "high_freight_category_names": _list_or_none(list(heavy["category"])),
        "freight_reduction": fmt_money(freight_reduction),
    }


def dq_summary(dq_log: pd.DataFrame) -> str:
    counts = dq_log.set_index("check")["rows_affected"]
    return (
        "Delivered orders without a delivery date: "
        f"{fmt_int(counts['orders_delivered_but_no_delivery_date'])}; with a delivery date "
        f"before the purchase date: {fmt_int(counts['orders_delivered_before_purchase'])} "
        "(both left out of lateness metrics). Products without a category: "
        f"{fmt_int(counts['products_missing_category'])}."
    )


def build_facts(
    results: dict[str, pd.DataFrame], dq_log: pd.DataFrame, params: Params, data_label: str
) -> dict[str, str]:
    """Compute every value the memo needs, formatted as text."""
    monthly = results["q01_monthly_orders_revenue"]
    delivered_orders = monthly["orders_delivered"].sum()
    revenue = float(monthly["revenue_delivered"].sum())
    aov = revenue / delivered_orders
    partial = monthly.loc[monthly["is_partial_month"] == 1, "purchase_month"]

    facts = {
        "data_label": data_label,
        "generated_on": date.today().isoformat(),
        "period_start": fmt_month(monthly["purchase_month"].min()),
        "period_end": fmt_month(monthly["purchase_month"].max()),
        "partial_months": ", ".join(fmt_month(m) for m in partial) or "none",
        "delivered_orders": fmt_int(delivered_orders),
        "revenue": fmt_money(revenue),
        "avg_order_value": fmt_money(aov),
        "dq_summary": dq_summary(dq_log),
        "late_rate_pct_by_timestamp": late_rate_by_timestamp(results, dq_log),
    }
    facts.update(delivery_facts(results, params))
    facts.update(customer_facts(results, aov))
    facts.update(category_facts(results, params))
    return facts


def render_memo(facts: dict[str, str], template_path: Path = MEMO_TEMPLATE) -> str:
    """Fill the template. Raises KeyError if the template uses a fact we did not compute."""
    return Template(template_path.read_text(encoding="utf-8")).substitute(facts)


def write_memo(facts: dict[str, str], out_dir: Path) -> Path:
    """Save the facts (for the optional AI draft) and the filled memo draft."""
    (out_dir / "memo_facts.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")
    memo_path = out_dir / "MEMO_draft.md"
    memo_path.write_text(render_memo(facts), encoding="utf-8")
    return memo_path
