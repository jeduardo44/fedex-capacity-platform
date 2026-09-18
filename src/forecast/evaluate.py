"""Backtesting and forecast accuracy metrics."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from src.forecast.base import BaseForecaster


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean absolute percentage error (%), ignoring zero actuals."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def backtest(
    forecaster_factory: Callable[[], BaseForecaster],
    df: pd.DataFrame,
    horizon: int,
) -> dict[str, float]:
    """Holdout backtest: train on all but the last ``horizon`` points,
    forecast the holdout, and score it.

    Args:
        forecaster_factory: zero-arg callable returning a fresh forecaster.
        df: series with columns ``ds`` and ``y``, sorted by ``ds``.
        horizon: number of trailing points to hold out.

    Returns:
        dict with ``mape`` and ``rmse`` (NaN when the series is too short).
    """
    if len(df) <= horizon + 2:
        return {"mape": float("nan"), "rmse": float("nan")}

    train, test = df.iloc[:-horizon], df.iloc[-horizon:]
    model = forecaster_factory().fit(train)
    pred = model.predict(horizon)

    merged = test.merge(pred, on="ds", how="inner")
    if merged.empty:
        # Frequency mismatch between predicted and actual timestamps:
        # fall back to positional alignment.
        n = min(len(test), len(pred))
        merged = pd.DataFrame(
            {"y": test["y"].to_numpy()[:n], "yhat": pred["yhat"].to_numpy()[:n]}
        )
    return {
        "mape": mape(merged["y"].to_numpy(), merged["yhat"].to_numpy()),
        "rmse": rmse(merged["y"].to_numpy(), merged["yhat"].to_numpy()),
    }
