"""Five static charts (PNG) for the README and the memo, drawn from the SQL results.

Style choices: one colour per chart unless colour carries meaning, light gridlines,
no top/right frame, values labelled directly where there are only a few bars.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to files only; no window needed (works in CI)
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.ticker import StrMethodFormatter  # noqa: E402

BLUE = "#2a78d6"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"
BLUES = LinearSegmentedColormap.from_list("blues", ["#cde2fb", "#5598e7", "#0d366b"])


def _new_axes(title: str, subtitle: str, size=(8, 4.5)):
    fig, ax = plt.subplots(figsize=size, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    fig.suptitle(title, x=0.02, ha="left", fontsize=13, color=INK, fontweight="bold")
    ax.set_title(subtitle, loc="left", fontsize=9, color=INK_SECONDARY)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)
    return fig, ax


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return path


def monthly_revenue(monthly: pd.DataFrame, path: Path) -> Path:
    full = monthly[monthly["is_partial_month"] == 0]
    fig, ax = _new_axes(
        "Monthly product revenue (delivered orders)",
        "BRL, item prices excluding freight; partial months left out",
    )
    ax.plot(
        pd.to_datetime(full["purchase_month"]),
        full["revenue_delivered"],
        color=BLUE,
        lw=2,
        marker="o",
        ms=4,
    )
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.set_ylim(bottom=0)
    # One tick per month, or fewer when there are many months.
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(full) // 8)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    return _save(fig, path)


def review_by_delay(buckets: pd.DataFrame, path: Path) -> Path:
    fig, ax = _new_axes(
        "Average review score by how late the order arrived",
        "Delivered orders with a review; n = orders in each group",
    )
    bars = ax.bar(buckets["delay_bucket"], buckets["avg_review"], color=BLUE, width=0.6)
    for bar, score, n in zip(
        bars, buckets["avg_review"], buckets["orders_with_review"], strict=True
    ):
        ax.annotate(
            f"{score:.2f}\nn={n:,}",
            (bar.get_x() + bar.get_width() / 2, score),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=INK_SECONDARY,
        )
    ax.set_ylim(0, 5.6)
    ax.set_ylabel("Average stars (1-5)", color=INK_SECONDARY, fontsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    return _save(fig, path)


def late_rate_by_state(states: pd.DataFrame, path: Path) -> Path:
    national = 100 * states["late_orders"].sum() / states["delivered_orders"].sum()
    shown = states[states["enough_orders"] == 1].sort_values("late_rate_pct")
    fig, ax = _new_axes(
        "Late-delivery rate by customer state",
        f"States with enough orders; dashed line = all states ({national:.1f}%)",
        size=(8, max(3.5, 0.28 * len(shown) + 1.5)),
    )
    ax.barh(shown["customer_state"], shown["late_rate_pct"], color=BLUE, height=0.6)
    ax.axvline(national, color=INK_SECONDARY, lw=1, ls="--")
    ax.set_xlabel(
        "% of delivered orders that arrived after the promised date",
        color=INK_SECONDARY,
        fontsize=9,
    )
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    return _save(fig, path)


def top_categories(categories: pd.DataFrame, path: Path) -> Path:
    top = categories.sort_values("revenue", ascending=False).head(10).iloc[::-1]
    fig, ax = _new_axes(
        "Top 10 categories by product revenue", "Delivered orders, BRL item prices", size=(8, 4.8)
    )
    ax.barh(top["category"], top["revenue"], color=BLUE, height=0.6)
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    return _save(fig, path)


def cohort_grid(cohorts: pd.DataFrame, min_cohort_size: int, last_month, months: int = 6):
    """Retention % per cohort (rows) and months later (columns 1..months).

    0 means "observed, nobody came back". NaN means "not observable yet" (the month is
    after the end of the data), which is different from 0 and is left blank in the chart.
    """
    sizes = cohorts[
        (cohorts["months_since_first"] == 0) & (cohorts["cohort_size"] >= min_cohort_size)
    ]
    grid = pd.DataFrame(
        index=pd.to_datetime(sizes["cohort_month"]), columns=range(1, months + 1), dtype=float
    )
    lookup = cohorts.set_index([pd.to_datetime(cohorts["cohort_month"]), "months_since_first"])[
        "retention_pct"
    ]
    for cohort in grid.index:
        for m in grid.columns:
            if cohort + pd.DateOffset(months=m) <= pd.Timestamp(last_month):
                grid.loc[cohort, m] = lookup.get((cohort, m), 0.0)
    return grid


def cohort_heatmap(cohorts: pd.DataFrame, min_cohort_size: int, last_month, path: Path) -> Path:
    grid = cohort_grid(cohorts, min_cohort_size, last_month)
    labels = [m.strftime("%Y-%m") for m in grid.index]
    fig, ax = _new_axes(
        "Cohort retention: % of customers buying again",
        "Rows = month of first delivered order; columns = months later; blank = not observable yet",
        size=(8, max(3.5, 0.3 * len(grid) + 1.5)),
    )
    values = grid.to_numpy(dtype=float)
    vmax = max(np.nanmax(values) if np.isfinite(values).any() else 0.0, 0.1)
    cmap = BLUES.with_extremes(bad=SURFACE)  # NaN cells use the background colour
    ax.imshow(np.ma.masked_invalid(values), cmap=cmap, aspect="auto", vmin=0, vmax=vmax)
    ax.set_xticks(range(grid.shape[1]), [str(m) for m in grid.columns])
    ax.set_yticks(range(len(labels)), labels)
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            if np.isnan(value):
                continue
            text_color = "white" if value > 0.6 * vmax else INK
            ax.text(
                col, row, f"{value:.2f}", ha="center", va="center", fontsize=7, color=text_color
            )
    ax.spines["bottom"].set_visible(False)
    return _save(fig, path)


def make_charts(results: dict[str, pd.DataFrame], min_cohort_size: int, charts_dir: Path):
    """Draw all five charts and return their paths."""
    charts_dir.mkdir(parents=True, exist_ok=True)
    return [
        monthly_revenue(results["q01_monthly_orders_revenue"], charts_dir / "monthly_revenue.png"),
        review_by_delay(results["q11_review_by_delay_bucket"], charts_dir / "review_by_delay.png"),
        late_rate_by_state(
            results["q04_late_delivery_by_state"], charts_dir / "late_rate_by_state.png"
        ),
        top_categories(results["q03_top_categories"], charts_dir / "top_categories.png"),
        cohort_heatmap(
            results["q07_cohort_retention"],
            min_cohort_size,
            results["q01_monthly_orders_revenue"]["purchase_month"].max(),
            charts_dir / "cohort_retention.png",
        ),
    ]
