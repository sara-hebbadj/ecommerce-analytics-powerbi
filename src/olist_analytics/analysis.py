"""Build the clean tables and the model, then answer each SQL question in sql/questions/."""

from pathlib import Path

import duckdb
import pandas as pd

from olist_analytics.config import QUESTIONS_DIR, SQL_DIR, Params

QUESTION_MARKER = "-- Question:"


def write_params(con: duckdb.DuckDBPyConnection, params: Params) -> None:
    """Store the thresholds in a one-row 'params' table so the SQL files can read them."""
    values = params.as_dict()
    columns = ", ".join(f"{int(value)} AS {name}" for name, value in values.items())
    con.execute(f"CREATE OR REPLACE TABLE params AS SELECT {columns}")


def build_tables(con: duckdb.DuckDBPyConnection, params: Params) -> None:
    """Run stage 1 (clean_*) and stage 2 (fact_* and dim_*)."""
    write_params(con, params)
    for stage in ("stage_1_clean.sql", "stage_2_model.sql"):
        con.execute((SQL_DIR / stage).read_text(encoding="utf-8"))


def question_files(questions_dir: Path = QUESTIONS_DIR) -> list[Path]:
    """All question files in order (q01, q02, ...)."""
    return sorted(questions_dir.glob("q*.sql"))


def question_text(sql_path: Path) -> str:
    """The plain-English question written in the file's header comment."""
    lines = sql_path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith(QUESTION_MARKER):
            text = line.removeprefix(QUESTION_MARKER).strip()
            # The question may wrap onto the next comment lines; it ends with "?".
            for more in lines[i + 1 :]:
                if text.endswith("?") or not more.startswith("--"):
                    break
                text += " " + more.removeprefix("--").strip()
            return text
    raise ValueError(f"{sql_path.name} has no '{QUESTION_MARKER}' header comment")


def run_questions(con: duckdb.DuckDBPyConnection, results_dir: Path) -> dict[str, pd.DataFrame]:
    """Run every question, save each answer as results/<file name>.csv, return them all."""
    results_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    index_rows = []
    for sql_path in question_files():
        df = con.execute(sql_path.read_text(encoding="utf-8")).fetchdf()
        df.to_csv(results_dir / f"{sql_path.stem}.csv", index=False)
        results[sql_path.stem] = df
        index_rows.append(
            {"file": sql_path.name, "question": question_text(sql_path), "rows": len(df)}
        )
    pd.DataFrame(index_rows).to_csv(results_dir / "_index.csv", index=False)
    return results
