# Demo

Two front ends show the same results:

- **Power BI dashboard**: the main demo for data-analyst roles, built by Sara with
  `docs/POWERBI_STEPS.md` (PDF export and `.pbit` template go in `powerbi/`).
- **`app/app.py`**: a small Gradio dashboard that runs as a Hugging Face Space
  (https://huggingface.co/spaces/sarahebbadj/ecommerce-analytics-powerbi). It reads only the
  committed, aggregated files in `outputs/` (CC BY-NC-SA 4.0, derived from the Olist data), never
  the raw data or the row-level database, and needs no API key.

```bash
pip install -e ".[app]"
python app/app.py        # then open http://127.0.0.1:7860
```

Demo video: pending, to be recorded by Sara.
