# FedEx Capacity & Demand Analysis Platform

A reusable, fully local data analytics platform: ingest variable data sources,
transform them with dbt, forecast capacity vs demand, and generate shareable
interactive HTML dashboards. No cloud, no servers, no IT dependencies.

## Architecture

```
raw files (CSV/Excel/API)                 config/sources.yml
        │                                        │
        ▼                                        │
  src/ingest  ──── Parquet ────►  DuckDB (data/warehouse.duckdb)
                                     │  raw schema
                                     ▼
                            dbt (staging → intermediate → marts)
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
             src/forecast                     dashboards/ (Quarto)
       (Prophet / statsforecast)          standalone interactive HTML
       writes forecasts.* tables          in dashboards/output/
```

## Quick start

```bash
# 1. Install dependencies (needs uv: brew install uv)
make setup

# 2. Generate dummy data for a smoke test
make sample-data

# 3. Run the full pipeline
make all

# 4. Open the dashboards
open dashboards/output/index.html
```

## Commands

| Command | What it does |
|---|---|
| `make ingest` | Ingest all sources from `config/sources.yml` into DuckDB (`raw` schema) |
| `make transform` | Run `dbt build` (models + tests + seeds) |
| `make forecast` | Run models from `config/forecasts.yml`, write `forecasts.*` tables |
| `make dashboard` | Render Quarto dashboards to `dashboards/output/` |
| `make all` | Full pipeline: ingest → transform → forecast → dashboard |
| `make test` | Python unit tests |
| `make clean` | Reset processed data, warehouse and dashboard output |

## Adding a new data source

1. Add an entry to `config/sources.yml` (type: `csv`, `excel` or `api`).
2. Drop the files in `data/raw/<source_name>/`.
3. Run `make ingest` — the data lands in `raw.<source_name>` in DuckDB.
4. Add a staging model (`dbt_project/models/staging/stg_<source_name>.sql`)
   plus its source entry in `_staging.yml`, then build marts on top.

New source *type* (e.g. Parquet, SFTP): subclass `BaseIngestor` in
`src/ingest/`, implement `read()`, register it in `src/ingest/registry.py`.

## Adding a new forecast

1. Make sure the target mart exists and exposes its time column as `period_date`.
2. Add an entry to `config/forecasts.yml` (table, target column, groups,
   frequency, horizon, models).
3. Run `make forecast`. Results land in `forecasts.<name>` and backtest
   metrics in `forecasts.<name>_metrics`.

New model: subclass `BaseForecaster` in `src/forecast/`, register it in
`MODEL_REGISTRY` in `src/forecast/runner.py`, and reference it by name in
the config.

## Sharing dashboards

`make dashboard` produces self-contained HTML files in `dashboards/output/`.
Copy them to a shared folder, attach to email, or post in Teams — they open
in any browser with full interactivity, no server required.

## Google Sheets export (optional)

`src/export/to_sheets.py` pushes summary tables to Google Sheets. It needs a
Google service account key: set `GSPREAD_SERVICE_ACCOUNT=/path/to/key.json`
and share the spreadsheet with the service account email. Keys are gitignored.

## Project layout

See `CLAUDE.md` for the full structure and design principles. In short:

- `src/` — Python: ingestion, forecasting, exports, utilities (all typed, Pydantic-validated config)
- `config/` — YAML definitions of sources and forecasts (the only place to touch for new use cases)
- `dbt_project/` — SQL transformations with tests and docs
- `dashboards/` — Quarto `.qmd` reports rendering Plotly charts from DuckDB
- `data/` — raw files, processed Parquet, DuckDB warehouse (all gitignored)
