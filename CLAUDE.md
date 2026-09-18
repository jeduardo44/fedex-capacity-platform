# CLAUDE.md — FedEx Capacity & Demand Analysis Platform

## Context

Reusable data analytics platform for a Capacity & Demand Analysis team at
FedEx, maintained by a Data Engineer (Python, dbt, SQL, GCP background).
Ingests variable data sources, transforms them, builds ML forecasting models,
and generates interactive dashboards — all running locally with no cloud
infrastructure or IT dependencies. Must stay modular and generic: new data
sources, KPIs, or forecasting targets should never require restructuring.

## Tech Stack (all free, all local)

| Layer | Tool |
|---|---|
| Storage | DuckDB (persistent file at `data/warehouse.duckdb`) |
| Raw file format | Parquet (`data/processed/`) |
| Transformations | dbt Core + dbt-duckdb |
| Orchestration | Python scripts + Makefile |
| ML / Forecasting | scikit-learn, Prophet, statsforecast |
| Dashboards | Quarto (Python + Plotly) → standalone HTML |
| Package management | uv |

## Key Design Principles

1. **Config-driven sources**: a new data source = a new entry in
   `config/sources.yml` + files dropped in `data/raw/<name>/`. The ingest
   runner routes to the right ingestor automatically.
2. **Ingestor pattern**: ingestors inherit from `src/ingest/base.py`
   (`validate() → read() → clean() → to_parquet() → load_to_duckdb()`,
   orchestrated by `run()`). New source type = one new file + one line in
   `src/ingest/registry.py`.
3. **dbt layers**: staging (1:1 with sources, rename/cast only) →
   intermediate (business logic) → marts (final tables). Marts expose their
   time column as `period_date` — the forecast runner relies on this.
4. **Forecasting is pluggable**: `config/forecasts.yml` defines what to
   forecast. Models implement `BaseForecaster` (`fit`/`predict` on ds/y
   frames) and register in `MODEL_REGISTRY` (`src/forecast/runner.py`).
   Results land in `forecasts.<name>`; backtest metrics in
   `forecasts.<name>_metrics`.
5. **Dashboards are static HTML**: Quarto renders `.qmd` → self-contained
   HTML in `dashboards/output/` (embed-resources: true). Shareable by
   email/Teams/folders, no server.
6. **Makefile is the single entry point**: `make ingest | transform |
   forecast | dashboard | all | clean | test | sample-data`.
7. **Everything in the warehouse**: after ingestion all data lives in DuckDB
   (schemas: `raw`, `staging`, `intermediate`, `marts`, `forecasts`, `seeds`).

## Conventions

- Python fully typed; Pydantic models validate all YAML config (`src/utils/config.py`).
- Logging via loguru (`src/utils/logger.py`), never print.
- DuckDB access through the context manager in `src/utils/duckdb_utils.py`;
  dbt uses its own connection via `dbt_project/profiles.yml` (path is
  relative — always run dbt from `dbt_project/`, which the Makefile does).
- Per-source and per-forecast error isolation: one failure never kills the
  whole pipeline run.
- dbt: `{{ ref() }}` everywhere, schema tests + YAML docs on all models.
  Custom `generate_schema_name` macro gives clean schema names (no
  `main_` prefix).
- `.gitignore` excludes `data/raw/`, `data/processed/`, `*.duckdb`,
  `dashboards/output/`, `.env`, service-account keys.

## Status

Skeleton complete and verified end-to-end: `make sample-data && make all`
runs ingestion (Excel + CSV dummy sources) → dbt build → Prophet/AutoARIMA
forecasts → three Quarto dashboards. Sample data generator:
`scripts/generate_sample_data.py`.
