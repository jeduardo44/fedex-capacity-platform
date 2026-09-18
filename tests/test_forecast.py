"""Unit tests for forecasting metrics and backtesting."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.forecast.base import BaseForecaster
from src.forecast.evaluate import backtest, mape, rmse


class NaiveForecaster(BaseForecaster):
    """Predicts the last observed value - fast, dependency-free test double."""

    name = "naive"

    def fit(self, df: pd.DataFrame) -> "NaiveForecaster":
        self._last_value = float(df["y"].iloc[-1])
        self._last_ds = df["ds"].iloc[-1]
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        ds = pd.date_range(
            start=self._last_ds, periods=horizon + 1, freq=self.frequency
        )[1:]
        return pd.DataFrame({"ds": ds, "yhat": [self._last_value] * horizon})


def test_mape() -> None:
    assert mape(np.array([100, 200]), np.array([110, 180])) == pytest.approx(10.0)


def test_mape_ignores_zero_actuals() -> None:
    assert mape(np.array([0, 100]), np.array([5, 110])) == pytest.approx(10.0)


def test_rmse() -> None:
    assert rmse(np.array([1, 2, 3]), np.array([1, 2, 3])) == 0.0
    assert rmse(np.array([0, 0]), np.array([3, 4])) == pytest.approx(np.sqrt(12.5))


def test_backtest_perfect_forecast_on_constant_series() -> None:
    df = pd.DataFrame(
        {"ds": pd.date_range("2026-01-05", periods=20, freq="W-MON"), "y": 100.0}
    )
    metrics = backtest(lambda: NaiveForecaster("W-MON", 52), df, horizon=4)
    assert metrics["mape"] == pytest.approx(0.0)
    assert metrics["rmse"] == pytest.approx(0.0)


def test_backtest_short_series_returns_nan() -> None:
    df = pd.DataFrame(
        {"ds": pd.date_range("2026-01-05", periods=5, freq="W-MON"), "y": 100.0}
    )
    metrics = backtest(lambda: NaiveForecaster("W-MON", 52), df, horizon=4)
    assert np.isnan(metrics["mape"]) and np.isnan(metrics["rmse"])
