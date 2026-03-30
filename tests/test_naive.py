import pandas as pd
import pytest

from src.models.naive import MovingAverage, SeasonalNaive


@pytest.fixture
def train_panel():
    """Simple 28-day panel for one cell."""
    dates = pd.date_range("2020-01-01", periods=28, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "h3_cell": "cell_a",
            "crash_count": [i % 7 + 1 for i in range(28)],  # Weekly pattern
            "day_of_week": [d.dayofweek for d in dates],
        }
    )


def test_seasonal_naive_uses_same_weekday(train_panel):
    model = SeasonalNaive(season_length=7)
    model.fit(train_panel)
    preds = model.predict(horizon=7)
    assert len(preds) == 7
    # Predictions should repeat the last week
    last_week = train_panel["crash_count"].iloc[-7:].values
    assert list(preds["predicted"].values) == list(last_week)


def test_moving_average_computes_mean(train_panel):
    model = MovingAverage(window=7)
    model.fit(train_panel)
    preds = model.predict(horizon=3)
    expected_mean = train_panel["crash_count"].iloc[-7:].mean()
    for v in preds["predicted"]:
        assert abs(v - expected_mean) < 1e-6


def test_predict_returns_correct_horizon(train_panel):
    model = SeasonalNaive(season_length=7)
    model.fit(train_panel)
    for h in [1, 7, 14]:
        assert len(model.predict(horizon=h)) == h
