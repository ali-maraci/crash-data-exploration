"""Build daily panel dataset from crash events."""

import pandas as pd


def build_daily_panel(events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate events to daily counts per H3 cell, zero-filling gaps."""
    df = events.dropna(subset=["h3_cell"]).copy()
    df["date"] = pd.to_datetime(df["CRASH_DATE"]).dt.normalize()

    # Aggregate
    agg = (
        df.groupby(["date", "h3_cell"])
        .agg(
            crash_count=("h3_cell", "size"),
            injury_crash_count=("INJURIES_TOTAL", lambda x: (x > 0).sum()),
            fatal_crash_count=("INJURIES_FATAL", lambda x: (x > 0).sum()),
        )
        .reset_index()
    )

    # Complete panel: all (date, cell) combinations
    all_dates = pd.date_range(agg["date"].min(), agg["date"].max(), freq="D")
    all_cells = agg["h3_cell"].unique()
    idx = pd.MultiIndex.from_product([all_dates, all_cells], names=["date", "h3_cell"])
    panel = pd.DataFrame(index=idx).reset_index()

    panel = panel.merge(agg, on=["date", "h3_cell"], how="left")
    for col in ["crash_count", "injury_crash_count", "fatal_crash_count"]:
        panel[col] = panel[col].fillna(0).astype(int)

    # Calendar features
    panel["day_of_week"] = panel["date"].dt.dayofweek  # 0=Monday
    panel["month"] = panel["date"].dt.month
    panel["is_weekend"] = panel["day_of_week"].isin([5, 6]).astype(int)
    panel["day_of_year"] = panel["date"].dt.dayofyear

    return panel.sort_values(["h3_cell", "date"]).reset_index(drop=True)


def add_lag_features(
    panel: pd.DataFrame, lags: list[int] | None = None
) -> pd.DataFrame:
    """Add per-cell lag features for crash_count and injury_crash_count."""
    if lags is None:
        lags = [1, 7, 14, 28]
    panel = panel.copy()
    for target in ["crash_count", "injury_crash_count"]:
        for lag in lags:
            panel[f"{target}_lag_{lag}"] = panel.groupby("h3_cell")[target].shift(lag)
    return panel


def add_rolling_features(
    panel: pd.DataFrame, windows: list[int] | None = None
) -> pd.DataFrame:
    """Add per-cell rolling mean and sum for crash_count and injury_crash_count."""
    if windows is None:
        windows = [7, 14, 28]
    panel = panel.copy()
    for target in ["crash_count", "injury_crash_count"]:
        for w in windows:
            grp = panel.groupby("h3_cell")[target]
            panel[f"{target}_roll_{w}_mean"] = grp.transform(
                lambda x: x.shift(1).rolling(w, min_periods=1).mean()
            )
            panel[f"{target}_roll_{w}_sum"] = grp.transform(
                lambda x: x.shift(1).rolling(w, min_periods=1).sum()
            )
    return panel
