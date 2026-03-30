import numpy as np
import pandas as pd

from src.h3_index import assign_h3

import h3

DOWNTOWN_CELL = h3.latlng_to_cell(41.8781, -87.6298, 8)


def test_assign_h3_adds_column():
    df = pd.DataFrame({"LATITUDE": [41.88], "LONGITUDE": [-87.63]})
    result = assign_h3(df, resolution=8)
    assert "h3_cell" in result.columns


def test_known_coordinate_maps_to_expected_cell():
    df = pd.DataFrame({"LATITUDE": [41.8781], "LONGITUDE": [-87.6298]})
    result = assign_h3(df, resolution=8)
    assert result["h3_cell"].iloc[0] == DOWNTOWN_CELL


def test_null_coordinates_get_none():
    df = pd.DataFrame({"LATITUDE": [np.nan], "LONGITUDE": [-87.63]})
    result = assign_h3(df, resolution=8)
    assert result["h3_cell"].iloc[0] is None


def test_out_of_bounds_coordinates_get_none():
    df = pd.DataFrame({"LATITUDE": [40.0], "LONGITUDE": [-87.63]})
    result = assign_h3(df, resolution=8)
    assert result["h3_cell"].iloc[0] is None
