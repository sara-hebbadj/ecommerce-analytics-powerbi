"""Smoke test for the dashboard in app/app.py (skipped when gradio is not installed, as in CI).

It reads the committed aggregated outputs in outputs/ only (no raw data, no network).
"""

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("gradio")
APP_PATH = Path(__file__).resolve().parents[1] / "app" / "app.py"


@pytest.fixture(scope="module")
def app():
    spec = importlib.util.spec_from_file_location("olist_dashboard", APP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dashboard_builds_and_shows_the_licence(app):
    assert app.build() is not None
    assert "CC BY-NC-SA 4.0" in app.LICENCE_NOTE and "Olist" in app.LICENCE_NOTE


def test_monthly_trend_can_hide_partial_months(app):
    label = list(app.MONTHLY_METRICS)[0]
    assert len(app.monthly_trend(label, True)) < len(app.monthly_trend(label, False))


def test_top_categories_respects_n_and_order(app):
    chart, table = app.top_categories(5, "Revenue", True)
    assert len(chart) == 5 and list(chart["value"]) == sorted(chart["value"], reverse=True)
    lowest, _ = app.top_categories(3, "Lowest average review", True)
    assert list(lowest["value"]) == sorted(lowest["value"])


def test_state_filter_and_retention(app):
    chart, table = app.late_by_state(1000)
    assert (table["delivered_orders"] >= 1000).all()
    assert set(app.retention_curve(1)["retention_pct"].between(0, 100)) == {True}
