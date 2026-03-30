import pandas as pd
import pytest

from src.models.lgbm import CrashForecaster


@pytest.fixture
def train_panel():
    """60-day panel for 2 cells with lag/rolling features."""
    dates = pd.date_range("2020-01-01", periods=60, freq="D")
    rows = []
    for d in dates:
        for cell in ["cell_a", "cell_b"]:
            rows.append(
                {
                    "date": d,
                    "h3_cell": cell,
                    "crash_count": (d.dayofweek + 1) + (1 if cell == "cell_a" else 0),
                    "injury_crash_count": 0,
                    "day_of_week": d.dayofweek,
                    "month": d.month,
                    "is_weekend": int(d.dayofweek >= 5),
                    "day_of_year": d.dayofyear,
                }
            )
    panel = pd.DataFrame(rows)
    # Add minimal lag features
    for lag in [1, 7]:
        panel[f"crash_count_lag_{lag}"] = panel.groupby("h3_cell")["crash_count"].shift(lag)
    panel["crash_count_roll_7_mean"] = panel.groupby("h3_cell")["crash_count"].transform(
        lambda x: x.shift(1).rolling(7, min_periods=1).mean()
    )
    return panel.dropna()


def test_fit_does_not_raise(train_panel):
    model = CrashForecaster(target="crash_count")
    model.fit(train_panel)


def test_predict_returns_correct_shape(train_panel):
    model = CrashForecaster(target="crash_count")
    model.fit(train_panel)
    preds = model.predict(train_panel, horizon=7)
    n_cells = train_panel["h3_cell"].nunique()
    assert len(preds) == 7 * n_cells


def test_predict_values_non_negative(train_panel):
    model = CrashForecaster(target="crash_count")
    model.fit(train_panel)
    preds = model.predict(train_panel, horizon=7)
    assert (preds["predicted"] >= 0).all()


def test_feature_importance_returns_dataframe(train_panel):
    model = CrashForecaster(target="crash_count")
    model.fit(train_panel)
    fi = model.feature_importance()
    assert "feature" in fi.columns
    assert "importance" in fi.columns


def test_save_and_load_roundtrip(train_panel, tmp_path):
    model = CrashForecaster(target="crash_count")
    model.fit(train_panel)
    preds_before = model.predict(train_panel, horizon=3)

    model.save(tmp_path / "model.txt")
    loaded = CrashForecaster.load(tmp_path / "model.txt", target="crash_count")
    preds_after = loaded.predict(train_panel, horizon=3)

    pd.testing.assert_frame_equal(preds_before, preds_after)
