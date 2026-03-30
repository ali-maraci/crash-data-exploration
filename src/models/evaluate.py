"""Forecasting evaluation metrics and rolling backtest."""

import math

import numpy as np
import pandas as pd


def mae(y_true, y_pred) -> float:
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true, y_pred) -> float:
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return float(math.sqrt(np.mean((y_true - y_pred) ** 2)))


def wape(y_true, y_pred) -> float:
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    total_actual = np.sum(np.abs(y_true))
    if total_actual == 0:
        return float("inf")
    return float(np.sum(np.abs(y_true - y_pred)) / total_actual)


def rolling_backtest(
    model_cls,
    model_kwargs: dict,
    panel: pd.DataFrame,
    n_splits: int,
    horizon: int,
    train_min_days: int,
) -> pd.DataFrame:
    """Expanding-window backtest. Returns DataFrame with split, date, actual, predicted."""
    dates = sorted(panel["date"].unique())
    total_days = len(dates)
    available = total_days - train_min_days - horizon
    step = max(1, available // n_splits)

    results = []
    for i in range(n_splits):
        split_point = train_min_days + i * step
        train_end = dates[split_point - 1]
        test_start = dates[split_point]
        test_end = dates[min(split_point + horizon - 1, total_days - 1)]

        train = panel[panel["date"] <= train_end]
        test = panel[(panel["date"] >= test_start) & (panel["date"] <= test_end)]

        model = model_cls(**model_kwargs)
        model.fit(train)
        preds = model.predict(horizon=len(test))

        for j, row in test.iterrows():
            pred_idx = (row["date"] - test_start).days
            if pred_idx < len(preds):
                results.append(
                    {
                        "split": i,
                        "date": row["date"],
                        "actual": row["crash_count"],
                        "predicted": preds["predicted"].iloc[pred_idx],
                    }
                )

    return pd.DataFrame(results)
