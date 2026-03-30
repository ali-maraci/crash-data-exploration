import math

import pandas as pd
import pytest

from src.models.evaluate import mae, rmse, rolling_backtest, wape


def test_mae_known_values():
    assert abs(mae([1, 2, 3], [1, 2, 4]) - 1 / 3) < 1e-6


def test_rmse_known_values():
    assert abs(rmse([1, 2, 3], [1, 2, 4]) - math.sqrt(1 / 3)) < 1e-6


def test_wape_known_values():
    assert abs(wape([10, 20], [12, 18]) - 4 / 30) < 1e-6


def test_wape_with_all_zeros():
    result = wape([0, 0], [1, 1])
    assert result == float("inf")


def test_backtest_produces_n_splits():
    from src.models.naive import MovingAverage

    dates = pd.date_range("2020-01-01", periods=90, freq="D")
    panel = pd.DataFrame(
        {
            "date": dates,
            "h3_cell": "cell_a",
            "crash_count": range(90),
            "day_of_week": [d.dayofweek for d in dates],
        }
    )
    results = rolling_backtest(
        model_cls=MovingAverage,
        model_kwargs={"window": 7},
        panel=panel,
        n_splits=3,
        horizon=7,
        train_min_days=30,
    )
    assert results["split"].nunique() == 3
