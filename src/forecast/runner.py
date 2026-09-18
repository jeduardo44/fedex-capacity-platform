"""Forecast runner: entry point for ``make forecast``.

Reads config/forecasts.yml, pulls each source mart from DuckDB, fits the
configured models per group, and writes results back to the warehouse:

- ``forecasts.<name>``          - future predictions (one row per group/model/date)
- ``forecasts.<name>_metrics``  - holdout backtest metrics per group/model
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import pandas as pd

from src.forecast.base import BaseForecaster
from src.forecast.evaluate import backtest
from src.forecast.prophet_model import ProphetForecaster
from src.forecast.stats_model import AutoArimaForecaster, EtsForecaster
from src.utils.config import ForecastConfig, load_forecasts
from src.utils.duckdb_utils import read_table, warehouse_connection, write_dataframe
from src.utils.logger import log

MODEL_REGISTRY: dict[str, type[BaseForecaster]] = {
    "prophet": ProphetForecaster,
    "autoarima": AutoArimaForecaster,
    "ets": EtsForecaster,
}

# Map config frequency -> (pandas offset alias, seasonal period)
FREQ_MAP: dict[str, tuple[str, int]] = {
    "D": ("D", 7),
    "W": ("W-MON", 52),
    "M": ("MS", 12),
}


def _load_series(cfg: ForecastConfig) -> pd.DataFrame:
    """Pull the source mart: one row per group per timestamp."""
    group_cols = ", ".join(cfg.group_by) + ", " if cfg.group_by else ""
    query = f"""
        SELECT {group_cols}date_col AS ds, SUM({cfg.target_column}) AS y
        FROM (
            SELECT *, CAST({_timestamp_expr(cfg)} AS DATE) AS date_col
            FROM {cfg.source_table}
        )
        GROUP BY ALL
        ORDER BY ALL
    """
    with warehouse_connection(read_only=True) as con:
        return read_table(con, query)


def _timestamp_expr(cfg: ForecastConfig) -> str:
    # Marts expose their time column as the first non-group, non-target date
    # column; by convention our marts name it ``period_date``.
    return "period_date"


def run_forecast(cfg: ForecastConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    freq_alias, season = FREQ_MAP[cfg.frequency]
    df = _load_series(cfg)
    df["ds"] = pd.to_datetime(df["ds"])

    groups = (
        list(df.groupby(cfg.group_by, sort=True)) if cfg.group_by else [((), df)]
    )
    run_ts = datetime.now(timezone.utc)
    pred_rows: list[pd.DataFrame] = []
    metric_rows: list[dict] = []

    for group_key, group_df in groups:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        series = group_df[["ds", "y"]].sort_values("ds").dropna().reset_index(drop=True)
        group_label = "/".join(map(str, group_key)) or "all"

        for model_name in cfg.models:
            model_cls = MODEL_REGISTRY[model_name]
            factory = lambda: model_cls(frequency=freq_alias, season_length=season)  # noqa: B023
            try:
                model = factory().fit(series)
                pred = model.predict(cfg.horizon)
                metrics = backtest(factory, series, cfg.horizon)
            except Exception as exc:  # noqa: BLE001 - isolate per-model failures
                log.error(
                    "[{}] model={} group={} failed: {}",
                    cfg.name, model_name, group_label, exc,
                )
                continue

            pred = pred.assign(model=model_name, _forecasted_at=run_ts)
            for col, val in zip(cfg.group_by, group_key):
                pred[col] = val
            pred_rows.append(pred)
            metric_rows.append(
                {
                    **dict(zip(cfg.group_by, group_key)),
                    "model": model_name,
                    "mape": metrics["mape"],
                    "rmse": metrics["rmse"],
                    "n_train": len(series),
                    "_forecasted_at": run_ts,
                }
            )
            log.info(
                "[{}] model={} group={} -> {} predictions (backtest MAPE={:.1f}%)",
                cfg.name, model_name, group_label, len(pred), metrics["mape"],
            )

    predictions = pd.concat(pred_rows, ignore_index=True) if pred_rows else pd.DataFrame()
    metrics_df = pd.DataFrame(metric_rows)
    return predictions, metrics_df


def main() -> int:
    forecasts = load_forecasts()
    if not forecasts:
        log.warning("No forecasts defined in config/forecasts.yml")
        return 0

    failures: list[str] = []
    for cfg in forecasts:
        try:
            log.info("[{}] forecasting {} ({} steps of {})",
                     cfg.name, cfg.source_table, cfg.horizon, cfg.frequency)
            predictions, metrics_df = run_forecast(cfg)
            if predictions.empty:
                raise RuntimeError("no model produced predictions")
            with warehouse_connection() as con:
                write_dataframe(con, predictions, f"forecasts.{cfg.name}")
                write_dataframe(con, metrics_df, f"forecasts.{cfg.name}_metrics")
            log.info("[{}] wrote {} rows to forecasts.{}",
                     cfg.name, len(predictions), cfg.name)
        except Exception as exc:  # noqa: BLE001 - isolate per-forecast failures
            log.error("[{}] forecast failed: {}", cfg.name, exc)
            failures.append(cfg.name)

    ok = len(forecasts) - len(failures)
    log.info("Forecasting finished: {}/{} forecasts succeeded", ok, len(forecasts))
    return 1 if ok == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
