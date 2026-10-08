# Evaluation in this project

This is an analytics project, so "evaluation" means checking that the numbers are right,
not scoring a model. There are three layers:

1. **Metric edge cases with known answers** (`tests/test_metrics.py`, `tests/test_cleaning.py`):
   a synthetic fixture where every answer was worked out by hand. Run `pytest`.
2. **Reconciliation** (`outputs/reconciliation.csv`, written by every pipeline run): the
   same total computed two independent ways must match (by month vs by category vs from
   the Power BI export files).
3. **Optional AI memo draft: number faithfulness** (`python -m olist_analytics.ai_draft`).
   A model writes a first draft of the memo from `outputs/memo_facts.json`; a deterministic
   checker lists every number in the draft that is not in the facts. Pass = zero
   unsupported numbers.

## Folders

| Folder | Contents |
|---|---|
| `evals/dry_run/` | Output of `--dry-run` with the **fake client**. Proves the plumbing only. **Not real results.** |
| `evals/ai_draft/` | Real model runs (created on the first live run): drafts, `number_check.csv`, `traces.jsonl` with model, tokens, cost and latency. |

## Commands

```
# offline, no key needed (uses the synthetic demo facts)
python -m olist_analytics.pipeline --demo
python -m olist_analytics.ai_draft --dry-run --facts outputs/synthetic_demo/memo_facts.json

# live, after the real pipeline run and with OPENROUTER_API_KEY + MODEL_CHEAP in Portfolio Projects/.env
python -m olist_analytics.ai_draft --model cheap
```

## Results of the real-data run (8 October 2026, coding agent)

| Layer | Result | Denominator | Evidence |
|---|---|---|---|
| Metric edge cases (synthetic fixture) | 50 passed, 0 failed | 50 tests | `pytest` |
| Reconciliation on the real Olist data | 7 of 7 match | 7 totals | `outputs/reconciliation.csv` |
| AI memo draft, number check (`openai/gpt-6-luna`, the `MODEL_CHEAP` model) | 3 of 3 drafts passed (0 unsupported numbers; 23, 24 and 25 numbers per draft) | 3 drafts, 1 call each | `evals/ai_draft/number_check.csv`, `traces.jsonl`, `memo_draft_*.md` |

- **Cost of the 3 live calls:** US$0.0017598 in total (0.0007151 + 0.0005056 + 0.0005391, from
  OpenRouter's `usage.cost` in `traces.jsonl`); 901 prompt tokens per call; latency 8.8–11.9 s.
- **What the number check cannot see** (coding agent's reading of the 3 drafts, not a
  measured score): none of the drafts mentions that 70.1% of late-order reviews were
  answered before the parcel arrived (a fact that was in `memo_facts.json`); draft 1 turns
  that fact into a vague recommendation about "customer-response handling"; all three quote
  revenue and freight without the currency (BRL). Every number was faithful, but the choice
  of what to say still needs a human, which is why Sara rewrites the memo herself.
- n = 3 drafts from one model on one set of facts, so this shows the checker works on real
  model output; it is not a general faithfulness rate.
