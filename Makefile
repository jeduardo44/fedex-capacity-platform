# FedEx Capacity & Demand Analysis Platform
# All commands run through uv so no manual venv activation is needed.

SHELL := /bin/bash
export DBT_PROFILES_DIR := $(CURDIR)/dbt_project

.PHONY: help setup sample-data ingest transform forecast dashboard all test lint clean

help:
	@echo "Available targets:"
	@echo "  make setup        - install all dependencies with uv"
	@echo "  make sample-data  - generate dummy raw files (demo / smoke test)"
	@echo "  make ingest       - ingest all sources from config/sources.yml into DuckDB"
	@echo "  make transform    - run dbt (staging -> intermediate -> marts) + tests"
	@echo "  make forecast     - run forecasting models from config/forecasts.yml"
	@echo "  make dashboard    - render Quarto dashboards to dashboards/output/"
	@echo "  make all          - full pipeline: ingest -> transform -> forecast -> dashboard"
	@echo "  make test         - run Python unit tests"
	@echo "  make clean        - remove processed data, warehouse and dashboard output"

setup:
	uv sync

sample-data:
	uv run python -m scripts.generate_sample_data

ingest:
	uv run python -m src.ingest.runner

transform:
	cd dbt_project && uv run dbt build

forecast:
	uv run python -m src.forecast.runner

dashboard:
	cd dashboards && uv run quarto render --output-dir output
	@echo "Dashboards written to dashboards/output/ - open index.html in a browser."

all: ingest transform forecast dashboard
	@echo "Full pipeline complete."

test:
	uv run pytest -v

lint:
	uv run ruff check src tests scripts

clean:
	rm -rf data/processed/* data/warehouse.duckdb data/warehouse.duckdb.wal
	rm -rf dashboards/output/* dbt_project/target dbt_project/logs
	touch data/processed/.gitkeep dashboards/output/.gitkeep
	@echo "Cleaned processed data, warehouse and dashboard output."
