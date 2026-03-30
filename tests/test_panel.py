import numpy as np
import pandas as pd
import pytest

from src.panel import add_lag_features, add_rolling_features, build_daily_panel


@pytest.fixture
def events_with_h3():
    """Small events DataFrame with h3_cell column for panel tests."""
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    rows = []
    for d in dates:
        for cell in ["cell_a", "cell_b"]:
            n_crashes = 2 if cell == "cell_a" else 1
            for _ in range(n_crashes):
                rows.append(
                    {
                        "CRASH_DATE": d,
                        "h3_cell": cell,
                        "INJURIES_TOTAL": 0,
                        "INJURIES_FATAL": 0,
                    }
                )
    # Remove crashes for cell_b on day index 5 to test zero-filling
    df = pd.DataFrame(rows)
    df = df[~((df["CRASH_DATE"] == dates[5]) & (df["h3_cell"] == "cell_b"))]
    return df


def test_daily_panel_has_no_missing_dates(events_with_h3):
    panel = build_daily_panel(events_with_h3)
    for cell in panel["h3_cell"].unique():
        cell_dates = panel[panel["h3_cell"] == cell]["date"]
        full_range = pd.date_range(cell_dates.min(), cell_dates.max(), freq="D")
        assert len(cell_dates) == len(full_range), f"Missing dates for {cell}"


def test_zero_fill(events_with_h3):
    panel = build_daily_panel(events_with_h3)
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    row = panel[(panel["h3_cell"] == "cell_b") & (panel["date"] == dates[5])]
    assert len(row) == 1
    assert row["crash_count"].iloc[0] == 0


def test_lag_features_shift_correctly(events_with_h3):
    panel = build_daily_panel(events_with_h3)
    panel = add_lag_features(panel, lags=[1])
    cell_a = panel[panel["h3_cell"] == "cell_a"].sort_values("date").reset_index(drop=True)
    # lag_1 of row i should equal crash_count of row i-1
    for i in range(1, len(cell_a)):
        assert cell_a.loc[i, "crash_count_lag_1"] == cell_a.loc[i - 1, "crash_count"]


def test_rolling_mean_value(events_with_h3):
    panel = build_daily_panel(events_with_h3)
    panel = add_rolling_features(panel, windows=[3])
    cell_a = panel[panel["h3_cell"] == "cell_a"].sort_values("date").reset_index(drop=True)
    # Rolling mean at row 3 should be mean of rows 0,1,2
    expected = cell_a.loc[:2, "crash_count"].mean()
    actual = cell_a.loc[3, "crash_count_roll_3_mean"]
    assert abs(actual - expected) < 1e-6


def test_panel_shape(events_with_h3):
    panel = build_daily_panel(events_with_h3)
    n_dates = panel["date"].nunique()
    n_cells = panel["h3_cell"].nunique()
    assert len(panel) == n_dates * n_cells
