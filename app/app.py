"""Interactive dashboard of the real Olist results (can run as a Hugging Face Space).

    pip install -e ".[app]"
    python app/app.py        then open http://127.0.0.1:7860

It reads only the committed, aggregated outputs in outputs/ (result tables, data-quality log, memo).
It never reads the raw Olist data or the row-level database, makes no AI calls and needs no API key.
Data: Brazilian E-Commerce Public Dataset by Olist (Kaggle, version 2), CC BY-NC-SA 4.0. The derived
tables are shared under the same licence (non-commercial, credit to Olist); the code is MIT.
"""

from __future__ import annotations

import json
from pathlib import Path

import gradio as gr
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUTPUTS = REPO / "outputs"
RESULTS = OUTPUTS / "results"

LICENCE_NOTE = (
    "**Data:** [Brazilian E-Commerce Public Dataset by Olist]"
    "(https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle, version 2), licensed "
    "[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Credit: **Olist**. "
    "Every table and number here is an aggregate derived from that data and is shared under the "
    "**same licence (non-commercial use only)**; no raw or row-level data is included. Code: MIT."
)
MONTHLY_METRICS = {
    "Revenue (BRL, delivered orders)": "revenue_delivered",
    "Orders delivered": "orders_delivered",
    "Orders placed": "orders_placed",
    "Average order value (BRL)": "avg_order_value",
}


def result(name: str) -> pd.DataFrame:
    """One SQL answer from outputs/results/, e.g. result("q01_monthly_orders_revenue")."""
    return pd.read_csv(RESULTS / f"{name}.csv")


FACTS = json.loads((OUTPUTS / "memo_facts.json").read_text(encoding="utf-8"))
MONTHLY = result("q01_monthly_orders_revenue").assign(
    month=lambda d: pd.to_datetime(d["purchase_month"]),
    partial=lambda d: d["is_partial_month"] == 1,
)
CATEGORIES = result("q03_top_categories")
STATES = result("q04_late_delivery_by_state")
COHORTS = result("q07_cohort_retention")


def kpi_markdown() -> str:
    f = FACTS
    return (
        "| Delivered orders | Revenue (BRL, item prices) | Average order value | Late deliveries | "
        f"Review: late vs on time | Repeat customers |\n|---|---|---|---|---|---|\n"
        f"| **{f['delivered_orders']}** | **{f['revenue']}** | **BRL {f['avg_order_value']}** | "
        f"**{f['late_rate_pct']}** of delivered orders | "
        f"**{f['avg_review_late']}** vs **{f['avg_review_on_time']}** "
        f"stars | **{f['repeat_rate_pct']}** of {f['customers']} customers |\n\n"
        f"Period: {f['period_start']} to {f['period_end']} (partial months: {f['partial_months']})."
    )


def monthly_trend(metric_label: str, hide_partial: bool) -> pd.DataFrame:
    column = MONTHLY_METRICS[metric_label]
    rows = MONTHLY[~MONTHLY["partial"]] if hide_partial else MONTHLY
    return rows[["month", column]].rename(columns={column: "value"})


def top_categories(
    top_n: int, rank_by: str, reliable_only: bool
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = CATEGORIES[CATEGORIES["enough_orders"] == 1] if reliable_only else CATEGORIES
    ascending = rank_by == "Lowest average review"
    column = "revenue" if rank_by == "Revenue" else "avg_review"
    rows = rows.sort_values(column, ascending=ascending).head(int(top_n))
    table = rows[
        ["category", "orders", "revenue", "revenue_share_pct", "avg_review", "reviewed_orders"]
    ]
    return rows[["category", column]].rename(columns={column: "value"}), table


def late_by_state(min_orders: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = STATES[STATES["delivered_orders"] >= int(min_orders)].sort_values(
        "late_rate_pct", ascending=False
    )
    return rows[["customer_state", "late_rate_pct"]], rows


def retention_curve(months_since_first: int) -> pd.DataFrame:
    """Share of each monthly cohort that bought again N months after its first delivered order."""
    rows = COHORTS[COHORTS["months_since_first"] == int(months_since_first)].copy()
    rows["cohort"] = pd.to_datetime(rows["cohort_month"])
    return rows[["cohort", "retention_pct", "cohort_size", "active_customers"]]


def build() -> gr.Blocks:
    with gr.Blocks(title="E-commerce analytics (Olist)") as demo:
        gr.Markdown(
            "# E-commerce analytics on the public Olist dataset\n"
            "DuckDB SQL over about 100,000 real orders from a Brazilian marketplace (2016 to "
            "2018): late deliveries and review scores, repeat customers, categories and freight. "
            "Every number comes from the pipeline's saved outputs; nothing is typed by hand. "
            "The Power BI version of this dashboard is "
            "described in the GitHub repo."
        )
        gr.Markdown(LICENCE_NOTE)
        with gr.Tab("Overview"):
            gr.Markdown(kpi_markdown())
            with gr.Row():
                metric = gr.Dropdown(
                    list(MONTHLY_METRICS), value=list(MONTHLY_METRICS)[0], label="Monthly metric"
                )
                hide_partial = gr.Checkbox(value=True, label="Hide partial months")
            trend = gr.LinePlot(
                monthly_trend(list(MONTHLY_METRICS)[0], True),
                x="month",
                y="value",
                title="Monthly trend",
                x_title="Purchase month",
                y_title="Value",
                height=360,
            )
            for control in (metric, hide_partial):
                control.change(monthly_trend, [metric, hide_partial], trend)
        with gr.Tab("Late delivery vs review score"):
            gr.Markdown(
                f"Late orders averaged **{FACTS['avg_review_late']}** stars against "
                f"**{FACTS['avg_review_on_time']}** for on-time orders (gap {FACTS['review_gap']}, "
                f"95% CI {FACTS['review_gap_ci_low']} to "
                f"{FACTS['review_gap_ci_high']}). This is an association, not proof of cause: "
                f"{FACTS['late_answered_before_delivery_pct']} of late orders were reviewed before "
                "the parcel arrived."
            )
            buckets = result("q11_review_by_delay_bucket")
            gr.BarPlot(
                buckets,
                x="delay_bucket",
                y="avg_review",
                title="Average review by days late",
                x_title="Delivery delay",
                y_title="Average review (1-5)",
                sort=list(buckets["delay_bucket"]),
                height=320,
            )
            gr.Dataframe(
                result("q05_review_late_vs_on_time"), label="Late vs on time", interactive=False
            )
            min_orders = gr.Slider(
                0, 2000, value=300, step=50, label="Only states with at least this many orders"
            )
            state_plot = gr.BarPlot(
                late_by_state(300)[0],
                x="customer_state",
                y="late_rate_pct",
                sort="-y",
                title="Late-delivery rate by customer state",
                x_title="State",
                y_title="Late rate (%)",
                height=320,
            )
            state_table = gr.Dataframe(
                late_by_state(300)[1], label="Late delivery by state", interactive=False
            )
            min_orders.change(late_by_state, min_orders, [state_plot, state_table])
            gr.Dataframe(
                result("q12_worst_routes"),
                label="Worst seller-state -> customer-state routes",
                interactive=False,
            )
        with gr.Tab("Repeat customers"):
            f = FACTS
            gr.Markdown(
                f"**{f['repeat_rate_pct']}** of {f['customers']} customers placed a second "
                "delivered order "
                f"({f['repeat_customers']} customers); {f['repeat_same_day_only']} of them "
                f"({f['repeat_same_day_only_pct']}) only ordered again on the same day (a split "
                "basket). Counting only later-day returns: "
                f"**{f['repeat_rate_later_day_pct']}**, after a median of "
                f"{f['median_days_to_later_order']} days. Counting by `customer_id` instead of "
                f"`customer_unique_id` would wrongly show {f['repeat_rate_by_customer_id']}."
            )
            months = gr.Slider(1, 12, value=1, step=1, label="Months after the first order")
            curve = gr.LinePlot(
                retention_curve(1),
                x="cohort",
                y="retention_pct",
                title="Retention by monthly cohort",
                x_title="Cohort (month of first order)",
                y_title="Bought again (%)",
                height=320,
            )
            months.change(retention_curve, months, curve)
            gr.Dataframe(
                result("q02_repeat_customer_rate"),
                label="Repeat-customer summary",
                interactive=False,
            )
        with gr.Tab("Top categories"):
            with gr.Row():
                top_n = gr.Slider(5, 30, value=10, step=1, label="How many categories")
                rank_by = gr.Radio(
                    ["Revenue", "Highest average review", "Lowest average review"],
                    value="Revenue",
                    label="Rank by",
                )
                reliable = gr.Checkbox(value=True, label="Only categories with enough orders")
            chart, table = top_categories(10, "Revenue", True)
            cat_plot = gr.BarPlot(
                chart,
                x="category",
                y="value",
                sort="-y",
                title="Categories",
                x_title="Category",
                y_title="Value",
                x_label_angle=-45,
                height=380,
            )
            cat_table = gr.Dataframe(table, interactive=False)
            for control in (top_n, rank_by, reliable):
                control.change(top_categories, [top_n, rank_by, reliable], [cat_plot, cat_table])
            gr.Markdown(
                f"Freight costs **{FACTS['freight_share_pct']}** of the item value overall. "
                "Heaviest "
                f"categories: {FACTS['high_freight_categories']}."
            )
            gr.Dataframe(
                result("q06_freight_share"), label="Freight share by category", interactive=False
            )
        with gr.Tab("Payments and basket"):
            gr.Dataframe(result("q09_payment_types"), label="Payment types", interactive=False)
            gr.Dataframe(result("q10_basket_size"), label="Basket size", interactive=False)
        with gr.Tab("Decision memo"):
            gr.Markdown((OUTPUTS / "MEMO_draft.md").read_text(encoding="utf-8"))
        with gr.Tab("Data quality and licence"):
            gr.Markdown(LICENCE_NOTE)
            gr.Dataframe(
                pd.read_csv(OUTPUTS / "dq_log.csv"),
                label="Data-quality checks",
                interactive=False,
                wrap=True,
            )
            gr.Dataframe(
                pd.read_csv(OUTPUTS / "reconciliation.csv"),
                label="Totals computed two ways",
                interactive=False,
                wrap=True,
            )
            gr.Dataframe(
                pd.read_csv(RESULTS / "_index.csv"),
                label="The 12 SQL questions",
                interactive=False,
                wrap=True,
            )
    return demo


if __name__ == "__main__":
    build().launch()
