"""Run the whole analysis with one command.

    python -m olist_analytics.pipeline               # real Olist data in data/raw/
    python -m olist_analytics.pipeline --check-only  # only check the downloaded files
    python -m olist_analytics.pipeline --demo        # synthetic test fixture, no download

Steps: check schema -> load raw CSVs into DuckDB -> clean -> build model -> data-quality
log -> 12 SQL questions -> Power BI CSVs -> reconciliation -> charts -> memo draft.
"""

import argparse
import sys
from pathlib import Path

import duckdb
import pandas as pd

from olist_analytics.analysis import build_tables, run_questions
from olist_analytics.charts import make_charts
from olist_analytics.config import (
    DEFAULT_OUT_DIR,
    DEFAULT_PARAMS,
    DEFAULT_RAW_DIR,
    DEMO_OUT_DIR,
    FIXTURE_DIR,
    FIXTURE_PARAMS,
    Params,
)
from olist_analytics.export_powerbi import export_powerbi_tables
from olist_analytics.load import load_raw_tables, locate_csv_folder
from olist_analytics.memo import build_facts, write_memo
from olist_analytics.quality import run_quality_checks
from olist_analytics.reconcile import reconcile
from olist_analytics.schema import SchemaError, check_raw_files

REAL_DATA_LABEL = "Olist Brazilian E-commerce public dataset (Kaggle)"
SYNTHETIC_LABEL = "SYNTHETIC TEST FIXTURE - NOT REAL RESULTS"


def check_schema(raw_dir: Path) -> Path:
    """Find the CSV folder and stop with a clear message if anything is missing."""
    csv_dir = locate_csv_folder(raw_dir)
    problems = check_raw_files(csv_dir)
    if problems:
        raise SchemaError(
            f"The raw folder {csv_dir} is not ready:\n  - "
            + "\n  - ".join(problems)
            + "\nSee data/README.md for the download steps."
        )
    return csv_dir


def run_pipeline(
    raw_dir: Path,
    out_dir: Path,
    params: Params = DEFAULT_PARAMS,
    data_label: str = REAL_DATA_LABEL,
    make_pngs: bool = True,
) -> dict:
    """Run every step and return the main outputs (used by the tests too)."""
    csv_dir = check_schema(raw_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "olist.duckdb"
    db_path.unlink(missing_ok=True)  # always rebuild from the raw files
    con = duckdb.connect(str(db_path))
    try:
        row_counts = load_raw_tables(con, csv_dir)
        pd.DataFrame(
            [{"table": f"raw_{name}", "rows": n} for name, n in row_counts.items()]
        ).to_csv(out_dir / "load_summary.csv", index=False)

        build_tables(con, params)
        dq_log = run_quality_checks(con)
        dq_log.to_csv(out_dir / "dq_log.csv", index=False)

        results = run_questions(con, out_dir / "results")
        export_powerbi_tables(con, results, out_dir / "powerbi")
    finally:
        con.close()

    reconciliation = reconcile(results, out_dir / "powerbi")
    reconciliation.to_csv(out_dir / "reconciliation.csv", index=False)

    charts = make_charts(results, params.min_cohort_size, out_dir / "charts") if make_pngs else []
    facts = build_facts(results, dq_log, params, data_label)
    memo_path = write_memo(facts, out_dir)
    return {
        "row_counts": row_counts,
        "dq_log": dq_log,
        "results": results,
        "reconciliation": reconciliation,
        "charts": charts,
        "facts": facts,
        "memo_path": memo_path,
    }


def _print_summary(outputs: dict, out_dir: Path) -> None:
    print("Rows loaded:", ", ".join(f"{k}={v:,}" for k, v in outputs["row_counts"].items()))
    flagged = outputs["dq_log"][outputs["dq_log"]["rows_affected"] > 0]
    print(f"Data-quality checks with findings: {len(flagged)} of {len(outputs['dq_log'])}")
    rec = outputs["reconciliation"]
    print(f"Reconciliation: {int(rec['matches'].sum())} of {len(rec)} checks match")
    for row in rec[~rec["matches"]].itertuples():
        print(f"  MISMATCH {row.metric}: SQL {row.sql_value} vs export {row.export_value}")
    print(f"Outputs written to {out_dir}")
    print(f"Memo draft: {outputs['memo_path']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Olist e-commerce analytics pipeline")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--check-only", action="store_true", help="only check the raw files")
    parser.add_argument(
        "--demo", action="store_true", help="run on the small synthetic test fixture"
    )
    parser.add_argument("--no-charts", action="store_true")
    args = parser.parse_args(argv)

    if args.demo:
        raw_dir, out_dir = FIXTURE_DIR, DEMO_OUT_DIR
        params, label = FIXTURE_PARAMS, SYNTHETIC_LABEL
        print(f"DEMO MODE: synthetic fixture -> {out_dir} (these are NOT real results)")
    else:
        raw_dir, out_dir = args.raw_dir, args.out_dir
        params, label = DEFAULT_PARAMS, REAL_DATA_LABEL

    try:
        csv_dir = check_schema(raw_dir)
    except SchemaError as err:
        print(err, file=sys.stderr)
        return 1
    if args.check_only:
        print(f"Schema OK: all 9 Olist files found with the expected columns in {csv_dir}")
        return 0

    outputs = run_pipeline(raw_dir, out_dir, params, label, make_pngs=not args.no_charts)
    _print_summary(outputs, out_dir)
    return 0 if outputs["reconciliation"]["matches"].all() else 2


if __name__ == "__main__":
    sys.exit(main())
