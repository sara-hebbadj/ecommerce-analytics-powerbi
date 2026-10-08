# SYNTHETIC test fixture (not real data)

These 9 tiny CSV files have **exactly the same file names and column names** as the Olist
dataset, but every row was **invented by hand** (by the coding agent, written by
`../make_fixture.py`) so that each row tests one rule and the right answers can be worked
out on paper. Nothing here comes from Olist or from any real person or shop. IDs are short
and readable (`o01`, `c01`, `uniq_A`, `p01`, `s01`) instead of Olist's 32-character hashes.

The `--demo` mode of the pipeline runs on these files: its outputs are labelled
"SYNTHETIC TEST FIXTURE - NOT REAL RESULTS" and are never real results.

## What each row is for

| Rows | Rule it tests |
|---|---|
| `o03` appears twice in orders and its item twice in items | exact duplicates are removed and counted |
| `o05` is `canceled` but has a delivery date | status wins: not delivered |
| `o07` delivered at 18:00 on the promised date | compare dates, not timestamps: on time |
| `o09` is `delivered` with no delivery date | counted in revenue, left out of lateness |
| `o12` delivered *before* it was purchased | counted in revenue, left out of lateness |
| `o10` is `shipped`, `o13` is `unavailable` | not delivered: left out of revenue |
| customers `c01..c13` map to people `uniq_A..uniq_H` | `customer_id` is per order; `customer_unique_id` is the person |
| `c01` zip prefix `1310` | leading zero restored to `01310` |
| `o04` has 2 items from 2 sellers; `o06` has 3 units of one product | basket size, multi-seller routes |
| `o99` in items has no order | orphan item dropped |
| `p04` has no category; `p05` (`pc_gamer`) has no English name | `unknown` and Portuguese fallback |
| products header spells `lenght` (as in the original Olist file) | misspelt columns are renamed |
| translation file starts with a byte-order mark | BOM stripped from the header |
| `o08` has two reviews (3 then 5) | latest review kept (5) |
| review `r06` is used for two orders | reused review_id counted |
| review for `o10` has score `6` | out-of-range score set to missing |
| review for `o02` contains a line break inside quotes | multi-line CSV fields load correctly |
| `o12` has no review | delivered order without review counted |
| `o05` pays with `not_defined` 0.00; `o12` pays 100 for 135 of goods + freight | payment checks |
| geolocation: one duplicate row and one point in Portugal | duplicates harmless; point outside Brazil ignored |

## Hand-worked answers (checked in `tests/test_metrics.py`)

- Delivered orders: 10 (`o01 o02 o03 o04 o06 o07 o08 o09 o11 o12`). Revenue BRL 1,970; freight 258 (13.10%).
- Monthly revenue: Jan 550, Feb 260, Mar 400, Apr 760.
- People with a delivered order: 7 (A–G). Repeat: A, C, E → 3/7 = 42.86%. By `customer_id`: 0%.
- Orders with usable delivery dates: 8; late: `o02` (+3 days) and `o04` (+10 days) → 25%.
- Average review: on time 4.50 (6 orders), late 1.50 (2 orders).
- January cohort: A, B, C (size 3); A returns in month 1, C in month 3.
