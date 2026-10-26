# M1 Jupyter Book report

## Build locally

Python 3.14 is the report build environment used for this snapshot.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
jupyter-book build .
```

The report notebook executes from the committed aggregate snapshot in `data/bao_snapshot.json`; the build does not crawl the web or read raw source files. Figures and tables are generated from that snapshot.

## Scope

The findings concern Bao's range `2508.02872`–`2508.07871` only. See the notebook and checklist for denominators, evidence, limitations, and pending work. The public Pages site is published from the `main` branch by GitHub Actions.
