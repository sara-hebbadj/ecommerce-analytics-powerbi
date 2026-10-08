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

Live AI results: **pending live run (needs OpenRouter key).** One call per run; the cost
is logged in `traces.jsonl`.
