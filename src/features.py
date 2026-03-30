"""Feature engineering for crash data — extracted from run_analysis.py:102-141."""

import calendar

import pandas as pd

WET_WEATHER = ["RAIN", "SNOW", "FREEZING RAIN/DRIZZLE", "SLEET/HAIL", "BLOWING SNOW"]
WET_SURFACE = ["WET", "SNOW OR SLUSH", "ICE"]
SEVERE_INJURIES = ["INCAPACITATING INJURY", "FATAL"]
DAY_MAP = {
    1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday",
    5: "Thursday", 6: "Friday", 7: "Saturday",
}
DAMAGE_MAP = {"$500 OR LESS": 1, "$501 - $1,500": 2, "OVER $1,500": 3}


def _time_period(hour: int) -> str:
    if 6 <= hour <= 9:
        return "Morning Rush"
    if 10 <= hour <= 15:
        return "Midday"
    if 16 <= hour <= 19:
        return "Evening Rush"
    if 20 <= hour <= 23:
        return "Night"
    return "Late Night"


def _speed_category(speed) -> str:
    if pd.isna(speed):
        return "Unknown"
    if speed <= 20:
        return "0-20 mph"
    if speed <= 30:
        return "21-30 mph"
    if speed <= 40:
        return "31-40 mph"
    return "45+ mph"


def add_binary_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["IS_WET_WEATHER"] = df["WEATHER_CONDITION"].isin(WET_WEATHER).astype(int)
    df["IS_WET_SURFACE"] = df["ROADWAY_SURFACE_COND"].isin(WET_SURFACE).astype(int)
    df["HAS_INJURY"] = (df["INJURIES_TOTAL"] > 0).astype(int)
    df["HAS_FATAL"] = (df["INJURIES_FATAL"] > 0).astype(int)
    df["IS_SEVERE"] = df["MOST_SEVERE_INJURY"].isin(SEVERE_INJURIES).astype(int)
    df["IS_WEEKEND"] = df["CRASH_DAY_OF_WEEK"].isin([1, 7]).astype(int)
    df["IS_DARK"] = df["LIGHTING_CONDITION"].str.contains("DARK", na=False).astype(int)
    return df


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["TIME_PERIOD"] = df["CRASH_HOUR"].apply(_time_period)
    if "CRASH_DAY_OF_WEEK" in df.columns:
        df["DAY_NAME"] = df["CRASH_DAY_OF_WEEK"].map(DAY_MAP)
    if "CRASH_MONTH" in df.columns:
        df["MONTH_NAME"] = df["CRASH_MONTH"].apply(lambda m: calendar.month_abbr[int(m)])
    return df


def add_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "POSTED_SPEED_LIMIT" in df.columns:
        df["SPEED_CATEGORY"] = df["POSTED_SPEED_LIMIT"].apply(_speed_category)
    if "DAMAGE" in df.columns:
        df["DAMAGE_LEVEL"] = df["DAMAGE"].map(DAMAGE_MAP)
    return df


def engineer_all(df: pd.DataFrame) -> pd.DataFrame:
    df = add_binary_flags(df)
    df = add_temporal_features(df)
    df = add_categorical_features(df)
    return df
