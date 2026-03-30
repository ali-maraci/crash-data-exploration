import pandas as pd

from src.ingest import clean, load_raw


def test_load_raw_returns_expected_columns(tmp_path):
    # Create a minimal CSV
    df = pd.DataFrame(
        {
            "CRASH_RECORD_ID": ["CR1"],
            "CRASH_DATE": ["01/01/2020 12:00:00 AM"],
            "CRASH_HOUR": [10],
            "CRASH_DAY_OF_WEEK": [4],
            "CRASH_MONTH": [1],
            "LATITUDE": [41.88],
            "LONGITUDE": [-87.63],
            "POSTED_SPEED_LIMIT": [30],
            "WEATHER_CONDITION": ["CLEAR"],
            "LIGHTING_CONDITION": ["DAYLIGHT"],
            "ROADWAY_SURFACE_COND": ["DRY"],
            "MOST_SEVERE_INJURY": ["NO INDICATION OF INJURY"],
            "INJURIES_TOTAL": [0],
            "INJURIES_FATAL": [0],
            "HIT_AND_RUN_I": ["N"],
            "DAMAGE": ["$500 OR LESS"],
            "DOORING_I": [None],
            "LANE_CNT": [None],
            "PRIM_CONTRIBUTORY_CAUSE": ["NOT APPLICABLE"],
        }
    )
    csv_path = tmp_path / "test.csv"
    df.to_csv(csv_path, index=False)

    result = load_raw(csv_path)
    assert "CRASH_RECORD_ID" in result.columns
    assert "CRASH_DATE" in result.columns
    assert pd.api.types.is_datetime64_any_dtype(result["CRASH_DATE"])


def test_clean_filters_years(small_crashes_df):
    result = clean(small_crashes_df, year_range=(2020, 2020))
    years = result["CRASH_DATE"].dt.year.unique()
    assert all(2020 <= y <= 2020 for y in years)


def test_clean_drops_unusable_columns(small_crashes_df):
    result = clean(small_crashes_df, year_range=(2020, 2020))
    assert "DOORING_I" not in result.columns
    assert "LANE_CNT" not in result.columns


def test_clean_fills_hit_and_run(small_crashes_df):
    result = clean(small_crashes_df, year_range=(2020, 2020))
    assert result["HIT_AND_RUN_I"].isna().sum() == 0


def test_clean_drops_null_hour_rows(small_crashes_df):
    df = small_crashes_df.copy()
    df.loc[0, "CRASH_HOUR"] = None
    result = clean(df, year_range=(2020, 2020))
    assert result["CRASH_HOUR"].isna().sum() == 0
