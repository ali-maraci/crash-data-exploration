import numpy as np
import pandas as pd

from src.features import (
    add_binary_flags,
    add_categorical_features,
    add_temporal_features,
    engineer_all,
)


def test_binary_flags_are_0_or_1(small_crashes_df):
    from src.ingest import clean

    df = clean(small_crashes_df, year_range=(2020, 2020))
    result = add_binary_flags(df)
    flag_cols = [
        "IS_WET_WEATHER",
        "IS_WET_SURFACE",
        "HAS_INJURY",
        "HAS_FATAL",
        "IS_SEVERE",
        "IS_WEEKEND",
        "IS_DARK",
    ]
    for col in flag_cols:
        assert set(result[col].unique()).issubset({0, 1}), f"{col} has non-binary values"


def test_wet_weather_categories():
    df = pd.DataFrame({"WEATHER_CONDITION": ["RAIN", "CLEAR", "SNOW", "CLOUDY"]})
    df["ROADWAY_SURFACE_COND"] = "DRY"
    df["INJURIES_TOTAL"] = 0
    df["INJURIES_FATAL"] = 0
    df["MOST_SEVERE_INJURY"] = "NO INDICATION OF INJURY"
    df["CRASH_DAY_OF_WEEK"] = 3
    df["LIGHTING_CONDITION"] = "DAYLIGHT"
    result = add_binary_flags(df)
    assert list(result["IS_WET_WEATHER"]) == [1, 0, 1, 0]


def test_time_period_assignment():
    df = pd.DataFrame({"CRASH_HOUR": [7, 12, 17, 22, 3]})
    result = add_temporal_features(df)
    expected = ["Morning Rush", "Midday", "Evening Rush", "Night", "Late Night"]
    assert list(result["TIME_PERIOD"]) == expected


def test_engineer_all_adds_expected_columns(small_crashes_df):
    from src.ingest import clean

    df = clean(small_crashes_df, year_range=(2020, 2020))
    result = engineer_all(df)
    expected_cols = [
        "IS_WET_WEATHER", "IS_WET_SURFACE", "HAS_INJURY", "HAS_FATAL",
        "IS_SEVERE", "IS_WEEKEND", "IS_DARK", "TIME_PERIOD", "DAY_NAME",
        "MONTH_NAME", "SPEED_CATEGORY", "DAMAGE_LEVEL",
    ]
    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"
