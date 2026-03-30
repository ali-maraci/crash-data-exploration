from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CRASHSCOPE_")

    # Paths
    raw_csv_path: Path = Path("Traffic_Crashes.csv")
    events_parquet_path: Path = Path("data/events.parquet")
    panel_parquet_path: Path = Path("data/panel_daily_res8.parquet")
    model_dir: Path = Path("models")

    # Data
    year_min: int = 2016
    year_max: int = 2023
    h3_resolution: int = 8

    # Model
    forecast_horizon: int = 7
    train_test_split_date: str = "2023-01-01"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]
