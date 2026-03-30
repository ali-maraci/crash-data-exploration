from config.settings import Settings


def test_default_settings():
    s = Settings()
    assert s.h3_resolution == 8
    assert s.year_min == 2016
    assert s.year_max == 2023
    assert s.forecast_horizon == 7


def test_settings_paths_are_path_objects():
    s = Settings()
    assert hasattr(s.raw_csv_path, "exists")
    assert hasattr(s.events_parquet_path, "exists")
