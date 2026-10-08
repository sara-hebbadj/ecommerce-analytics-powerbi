"""Paths and analysis thresholds, kept in one place so they are easy to find and change."""

from dataclasses import asdict, dataclass
from pathlib import Path

# src/olist_analytics/config.py -> parents[2] is the repo folder.
REPO_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = REPO_ROOT / "sql"
QUESTIONS_DIR = SQL_DIR / "questions"
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "raw"
DEFAULT_OUT_DIR = REPO_ROOT / "outputs"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "olist_synthetic"
DEMO_OUT_DIR = DEFAULT_OUT_DIR / "synthetic_demo"
MEMO_TEMPLATE = REPO_ROOT / "memo" / "MEMO_TEMPLATE.md"


@dataclass(frozen=True)
class Params:
    """Minimum group sizes before a group is ranked or called "worst".

    Small groups give noisy rates: 2 late orders out of 3 is "67% late" but means little.
    The defaults are judgement calls for the ~100k-order Olist data; tests use 1.
    """

    min_category_orders: int = 100  # categories ranked by review score / freight share
    min_state_orders: int = 100  # states eligible for "worst states"
    min_route_orders: int = 50  # seller-state -> customer-state routes
    min_seller_orders: int = 30  # sellers in the ranking
    min_cohort_size: int = 100  # cohorts shown in the retention chart
    worst_states_for_what_if: int = 5  # memo what-if: how many worst states to "fix"

    def as_dict(self) -> dict:
        return asdict(self)


DEFAULT_PARAMS = Params()

# Used for the synthetic fixture (tests and --demo): every group counts.
FIXTURE_PARAMS = Params(
    min_category_orders=1,
    min_state_orders=1,
    min_route_orders=1,
    min_seller_orders=1,
    min_cohort_size=1,
)
