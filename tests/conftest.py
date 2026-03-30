import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def small_crashes_df():
    """500-row synthetic DataFrame mimicking Traffic_Crashes.csv schema."""
    rng = np.random.default_rng(42)
    n = 500
    dates = pd.date_range("2020-01-01", periods=60, freq="D")

    return pd.DataFrame(
        {
            "CRASH_RECORD_ID": [f"CR{i:06d}" for i in range(n)],
            "CRASH_DATE": rng.choice(dates, n),
            "CRASH_HOUR": rng.integers(0, 24, n),
            "CRASH_DAY_OF_WEEK": rng.integers(1, 8, n),
            "CRASH_MONTH": rng.integers(1, 13, n),
            "POSTED_SPEED_LIMIT": rng.choice([15, 20, 25, 30, 35, 40, 45, 50], n),
            "WEATHER_CONDITION": rng.choice(
                ["CLEAR", "RAIN", "SNOW", "CLOUDY", "UNKNOWN", None],
                n,
                p=[0.5, 0.15, 0.05, 0.15, 0.1, 0.05],
            ),
            "LIGHTING_CONDITION": rng.choice(
                ["DAYLIGHT", "DARKNESS", "DARK - LIGHTED", "DAWN", "DUSK"], n
            ),
            "ROADWAY_SURFACE_COND": rng.choice(
                ["DRY", "WET", "SNOW OR SLUSH", "ICE", "UNKNOWN"], n
            ),
            "MOST_SEVERE_INJURY": rng.choice(
                [
                    "NO INDICATION OF INJURY",
                    "NONINCAPACITATING INJURY",
                    "INCAPACITATING INJURY",
                    "FATAL",
                    "REPORTED, NOT EVIDENT",
                ],
                n,
                p=[0.6, 0.2, 0.1, 0.02, 0.08],
            ),
            "INJURIES_TOTAL": rng.choice([0, 0, 0, 1, 1, 2, 3], n),
            "INJURIES_FATAL": rng.choice([0, 0, 0, 0, 0, 0, 1], n),
            "HIT_AND_RUN_I": rng.choice(["Y", "N", None], n, p=[0.3, 0.6, 0.1]),
            "PRIM_CONTRIBUTORY_CAUSE": rng.choice(
                [
                    "FAILING TO YIELD RIGHT-OF-WAY",
                    "FOLLOWING TOO CLOSELY",
                    "IMPROPER OVERTAKING/PASSING",
                    "DISREGARDING TRAFFIC SIGNALS",
                    "NOT APPLICABLE",
                ],
                n,
            ),
            "DAMAGE": rng.choice(
                ["$500 OR LESS", "$501 - $1,500", "OVER $1,500"], n
            ),
            "LATITUDE": rng.uniform(41.68, 42.02, n),
            "LONGITUDE": rng.uniform(-87.91, -87.53, n),
            "DOORING_I": [None] * n,
            "LANE_CNT": [None] * n,
        }
    )


@pytest.fixture
def small_events_df(small_crashes_df):
    """Cleaned + feature-engineered events (requires src.ingest and src.features)."""
    from src.features import engineer_all
    from src.ingest import clean

    cleaned = clean(small_crashes_df, year_range=(2020, 2020))
    return engineer_all(cleaned)


@pytest.fixture
def small_panel_df(small_events_df):
    """Daily panel built from small_events_df (requires src.h3_index and src.panel)."""
    from src.h3_index import assign_h3
    from src.panel import add_lag_features, add_rolling_features, build_daily_panel

    events = assign_h3(small_events_df, resolution=8)
    panel = build_daily_panel(events)
    panel = add_lag_features(panel)
    panel = add_rolling_features(panel)
    return panel


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Temporary directory for test artifacts."""
    d = tmp_path / "data"
    d.mkdir()
    return d
