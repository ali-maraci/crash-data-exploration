"""End-to-end pipeline orchestrator."""

import logging
import sys
from pathlib import Path

import pandas as pd

from config.settings import Settings
from src.features import engineer_all
from src.h3_index import assign_h3
from src.ingest import clean, load_raw
from src.models.evaluate import mae, rmse, wape
from src.models.lgbm import CrashForecaster
from src.models.naive import MovingAverage, SeasonalNaive
from src.panel import add_lag_features, add_rolling_features, build_city_panel, build_daily_panel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def run_data_pipeline(settings: Settings | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ingest -> clean -> features -> H3 -> panel -> save parquet."""
    settings = settings or Settings()

    logger.info("Loading raw data from %s", settings.raw_csv_path)
    raw = load_raw(settings.raw_csv_path)
    cleaned = clean(raw, year_range=(settings.year_min, settings.year_max))
    events = engineer_all(cleaned)
    events = assign_h3(events, resolution=settings.h3_resolution)

    # Save events
    settings.events_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    events.to_parquet(settings.events_parquet_path, index=False)
    logger.info("Saved %d events to %s", len(events), settings.events_parquet_path)

    # Build panel
    panel = build_daily_panel(events)
    panel = add_lag_features(panel)
    panel = add_rolling_features(panel)
    panel.to_parquet(settings.panel_parquet_path, index=False)
    logger.info("Saved panel (%d rows) to %s", len(panel), settings.panel_parquet_path)

    # Build city-level panel
    city_panel = build_city_panel(panel)
    city_panel.to_parquet(settings.city_panel_parquet_path, index=False)
    logger.info("Saved city panel (%d rows) to %s", len(city_panel), settings.city_panel_parquet_path)

    return events, panel


def run_training_pipeline(settings: Settings | None = None):
    """Load panel -> split -> train baselines + LightGBM -> evaluate -> save."""
    settings = settings or Settings()

    panel = pd.read_parquet(settings.panel_parquet_path)
    split_date = pd.Timestamp(settings.train_test_split_date)
    train = panel[panel["date"] < split_date]
    test = panel[panel["date"] >= split_date]

    logger.info("Train: %d rows, Test: %d rows (split at %s)", len(train), len(test), split_date)

    # Train cell-level LightGBM
    model = CrashForecaster(target="crash_count")
    model.fit(train.dropna())

    settings.model_dir.mkdir(parents=True, exist_ok=True)
    model.save(settings.model_dir / "lgbm_cell_v1.txt")
    logger.info("Cell model saved to %s", settings.model_dir / "lgbm_cell_v1.txt")

    # Train city-level LightGBM
    city_panel = pd.read_parquet(settings.city_panel_parquet_path)
    city_train = city_panel[city_panel["date"] < split_date]
    city_model = CrashForecaster(target="crash_count")
    city_model.fit(city_train.dropna())
    city_model.save(settings.model_dir / "lgbm_city_v1.txt")
    logger.info("City model saved to %s", settings.model_dir / "lgbm_city_v1.txt")

    return model


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    settings = Settings()

    if cmd in ("data", "all"):
        run_data_pipeline(settings)
    if cmd in ("train", "all"):
        run_training_pipeline(settings)
