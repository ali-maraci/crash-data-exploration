"""Load and clean Chicago crash data."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_raw(path: Path) -> pd.DataFrame:
    """Load raw CSV with date parsing."""
    df = pd.read_csv(path, parse_dates=["CRASH_DATE"], low_memory=False)
    logger.info("Loaded %d rows from %s", len(df), path)
    return df


def clean(df: pd.DataFrame, year_range: tuple[int, int] = (2016, 2023)) -> pd.DataFrame:
    """Filter years, drop unusable columns, fill nulls, drop incomplete rows."""
    df = df.copy()
    df["CRASH_YEAR"] = df["CRASH_DATE"].dt.year
    df = df[df["CRASH_YEAR"].between(year_range[0], year_range[1])]

    df = df.drop(columns=["DOORING_I", "LANE_CNT"], errors="ignore")
    df["HIT_AND_RUN_I"] = df["HIT_AND_RUN_I"].fillna("N")
    df = df.dropna(subset=["CRASH_HOUR", "CRASH_DAY_OF_WEEK"])

    logger.info("Cleaned to %d rows (years %d-%d)", len(df), *year_range)
    return df.reset_index(drop=True)
