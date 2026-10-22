"""Hotspot helpers: valid accident points and a simple fixed-size grid count.

This is a descriptive concentration of *recorded* accidents. It is not statistical
clustering and does not predict future risk.
"""
import numpy as np
import pandas as pd

from utils.analytics import valid_coordinate_mask

DEFAULT_CELL_SIZE_DEG = 0.05   # about 5.5 km north-south


def accident_points(acc: pd.DataFrame, loc: pd.DataFrame = None) -> pd.DataFrame:
    """Accidents with valid coordinates. Missing accident coordinates fall back to locations.csv."""
    points = acc[["Accident_ID", "Date", "Severity", "Latitude", "Longitude", "Is_Synthetic"]].copy()
    if loc is not None and not loc.empty:
        fallback = loc.drop_duplicates("Accident_ID").set_index("Accident_ID")[["Latitude", "Longitude"]]
        for col in ("Latitude", "Longitude"):
            filled = points["Accident_ID"].map(fallback[col])
            points[col] = points[col].fillna(filled)
    return points[valid_coordinate_mask(points)].reset_index(drop=True)


def grid_counts(points: pd.DataFrame, cell_size: float = DEFAULT_CELL_SIZE_DEG) -> pd.DataFrame:
    """Count accidents per square grid cell of `cell_size` degrees. Returns one row per non-empty cell."""
    cols = ["Cell_Lat", "Cell_Lon", "Accidents", "Fatal"]
    if points.empty:
        return pd.DataFrame(columns=cols)
    if cell_size <= 0:
        raise ValueError("cell_size must be positive")
    work = pd.DataFrame({
        "row": np.floor(points["Latitude"].astype(float) / cell_size).astype(int),
        "col": np.floor(points["Longitude"].astype(float) / cell_size).astype(int),
        "fatal": points["Severity"].astype(str).str.strip().str.lower().isin(["fatal", "fatal injury"]).astype(int),
    })
    grouped = work.groupby(["row", "col"]).agg(Accidents=("fatal", "size"), Fatal=("fatal", "sum")).reset_index()
    grouped["Cell_Lat"] = ((grouped["row"] + 0.5) * cell_size).round(6)   # cell centre
    grouped["Cell_Lon"] = ((grouped["col"] + 0.5) * cell_size).round(6)
    return grouped[cols].sort_values("Accidents", ascending=False).reset_index(drop=True)
