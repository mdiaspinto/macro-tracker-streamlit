# 🥗 Macro Tracker (Streamlit)

A small nutrition **data app** for importing foods, logging what you eat, and analysing your daily calories and macronutrients.

![CI](https://github.com/mdiaspinto/macro-tracker-streamlit/actions/workflows/ci.yml/badge.svg)

## Introduction

I originally built this macro tracker as a personal project to keep track of my own daily nutrition. For this assignment I took that personal app and adapted it into a Python/Streamlit application, then restructured it so the data logic is cleanly separated, unit-tested, containerised, and reproducible. The result is the same idea I use myself, repackaged to demonstrate the deployment practices asked for in the brief: a Streamlit UI, a Docker container, tests on the data importing and filtering functions, and a CI pipeline.

## What it does

- **Import foods** three ways: an [Open Food Facts](https://world.openfoodfacts.org/)
  online lookup, a bundled offline foods table (~70 foods, per-100g macros), or a
  **CSV upload** of a whole food log.
- **Filter and aggregate** the log by date range and by *eaten vs. what-if*, into
  daily calorie and macro series.
- **Visualise** calories and protein/carbs/fat per day with interactive Plotly charts.
- **Estimate targets** with the Mifflin-St Jeor equation (BMR, then an activity
  factor for TDEE, then a lean/cut and bulk/gain split).

## Architecture

All analysis logic lives in the importable `macro_tracker` package, kept free of
any Streamlit/UI code so it can be tested directly. `app.py` is a thin UI layer.

| Module | Responsibility | Tested in |
|---|---|---|
| `macro_tracker/foods.py` | **Data importing**: offline lookup, Open Food Facts fetch/parse, portion scaling | `tests/test_foods.py` |
| `macro_tracker/data.py` | **Filtering / aggregation**: CSV import, date/eaten filters, daily series | `tests/test_data.py` |
| `macro_tracker/nutrition.py` | Calorie and target math (Mifflin-St Jeor) | `tests/test_nutrition.py` |
| `app.py` | Streamlit UI | not unit-tested |

The Open Food Facts call is hidden behind an **injectable `fetcher`**, so the
import tests run fully offline and CI never depends on a third-party API.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app.py            # http://localhost:8501
```

Try it with the bundled `data/sample_log.csv` via the sidebar uploader.

## Test & lint

```bash
ruff check .
pytest -v
```

## Run with Docker

```bash
docker build -t macro-tracker .
docker run --rm -p 8501:8501 macro-tracker   # http://localhost:8501
```

Or pull the pre-built image from GitHub Container Registry (published by CI on
every push to `main`):

```bash
docker pull ghcr.io/mdiaspinto/macro-tracker-streamlit:latest
docker run --rm -p 8501:8501 ghcr.io/mdiaspinto/macro-tracker-streamlit:latest
```

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push/PR:

1. **Lint** with `ruff` and **test** with `pytest` on Python 3.11 and 3.12.
2. **Build** the Docker image and **smoke-test** that the container becomes healthy.
3. On `main`, **publish** the image to GHCR tagged `latest` and the commit SHA.

## Reproducibility

- Pinned dependencies (`requirements.txt`, `requirements-dev.txt`).
- Pinned Python base image (`python:3.11-slim`) and a non-root container user.
- Deterministic, network-free tests; config in `pyproject.toml`.

## Data & formula provenance

The offline foods table, the calorie formula (`4/4/9` kcal per g of P/C/F), and
the Mifflin-St Jeor target math are ported verbatim from the original app so the
numbers match. Online macro data comes from Open Food Facts (ODbL).
