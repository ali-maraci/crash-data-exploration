"""Assign H3 hexagonal cells to crash events."""

import h3
import pandas as pd

# Chicago bounding box (approximate)
CHI_LAT_MIN, CHI_LAT_MAX = 41.64, 42.03
CHI_LON_MIN, CHI_LON_MAX = -87.94, -87.52


def _to_h3(row, resolution: int) -> str | None:
    lat, lon = row["LATITUDE"], row["LONGITUDE"]
    if pd.isna(lat) or pd.isna(lon):
        return None
    if not (CHI_LAT_MIN <= lat <= CHI_LAT_MAX and CHI_LON_MIN <= lon <= CHI_LON_MAX):
        return None
    return h3.latlng_to_cell(lat, lon, resolution)


def assign_h3(df: pd.DataFrame, resolution: int = 8) -> pd.DataFrame:
    """Add h3_cell column. Rows outside Chicago or with null coords get None."""
    df = df.copy()
    df["h3_cell"] = df.apply(_to_h3, axis=1, resolution=resolution)
    return df
