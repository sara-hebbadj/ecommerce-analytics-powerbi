"""Shared test fixtures. All tests use the SYNTHETIC fixture in tests/fixtures/olist_synthetic/.

No test reads real Olist data, calls a network service or needs an API key.
"""

import duckdb
import pytest

from olist_analytics.analysis import build_tables
from olist_analytics.config import FIXTURE_DIR, FIXTURE_PARAMS, Params
from olist_analytics.load import load_raw_tables
from olist_analytics.pipeline import SYNTHETIC_LABEL, run_pipeline


@pytest.fixture(scope="session")
def pipeline_outputs(tmp_path_factory):
    """Run the whole pipeline once on the synthetic fixture (charts included)."""
    out_dir = tmp_path_factory.mktemp("outputs")
    outputs = run_pipeline(FIXTURE_DIR, out_dir, FIXTURE_PARAMS, SYNTHETIC_LABEL)
    outputs["out_dir"] = out_dir
    return outputs


@pytest.fixture(scope="session")
def results(pipeline_outputs):
    """The SQL answers, keyed by file name (e.g. 'q01_monthly_orders_revenue')."""
    return pipeline_outputs["results"]


@pytest.fixture(scope="session")
def db(pipeline_outputs):
    """Read-only connection to the DuckDB file the pipeline built."""
    con = duckdb.connect(str(pipeline_outputs["out_dir"] / "olist.duckdb"), read_only=True)
    yield con
    con.close()


@pytest.fixture
def build_db():
    """Factory: a fresh in-memory database built from the fixture with chosen params."""

    def _build(params: Params = FIXTURE_PARAMS) -> duckdb.DuckDBPyConnection:
        con = duckdb.connect()
        load_raw_tables(con, FIXTURE_DIR)
        build_tables(con, params)
        return con

    return _build
