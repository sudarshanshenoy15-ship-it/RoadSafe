"""CSV loading and safe writing.

Rules: UTF-8, blanks stay missing (never zero), extra source columns are preserved,
and writes go to a temp file first, then replace the target.
"""
import logging
import os
import tempfile
from pathlib import Path

import pandas as pd

log = logging.getLogger("roadsafe")

SCHEMAS = {
    "accidents.csv": [
        "Accident_ID", "Date", "Time", "Latitude", "Longitude", "Severity",
        "Number_of_Casualties", "Number_of_Vehicles", "Data_Source", "Is_Synthetic",
    ],
    "vehicles.csv": [
        "Vehicle_ID", "Accident_ID", "Vehicle_Type", "Vehicle_Count", "Speed_Limit",
        "Vehicle_Movement", "Data_Source", "Is_Synthetic",
    ],
    "locations.csv": [
        "Location_ID", "Accident_ID", "Latitude", "Longitude", "Road_Type",
        "Road_Condition", "Lighting_Condition", "Traffic_Density", "Data_Source", "Is_Synthetic",
    ],
    "conditions_casualties.csv": [
        "Record_ID", "Accident_ID", "Weather", "Visibility", "Casualties", "Fatalities",
        "Injuries", "Risk_Factor", "Data_Source", "Is_Synthetic",
    ],
}

INT_COLUMNS = ["Number_of_Casualties", "Number_of_Vehicles", "Vehicle_Count",
               "Casualties", "Fatalities", "Injuries"]
FLOAT_COLUMNS = ["Latitude", "Longitude", "Speed_Limit"]


class DataError(Exception):
    """A file problem (missing, unreadable, wrong columns, cannot write)."""


class ValidationError(Exception):
    """One or more record-level validation problems."""

    def __init__(self, errors):
        self.errors = [errors] if isinstance(errors, str) else list(errors)
        super().__init__("; ".join(self.errors))


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric columns (blank -> missing) and tidy the Is_Synthetic text."""
    df = df.copy()
    for col in INT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in FLOAT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    if "Is_Synthetic" in df.columns:
        df["Is_Synthetic"] = df["Is_Synthetic"].astype(str).str.strip().str.lower()
    return df


def load_table(path, filename: str) -> pd.DataFrame:
    """Read one project CSV. Raises DataError with a readable message on problems."""
    path = Path(path)
    columns = SCHEMAS[filename]
    if not path.exists():
        raise DataError(
            f"{filename} was not found in {path.parent}. "
            "Run `python scripts/generate_sample_data.py` to create the sample data."
        )
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    except pd.errors.EmptyDataError:
        return coerce_types(pd.DataFrame(columns=columns))
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        log.exception("Could not parse %s", path)
        raise DataError(f"{filename} could not be read as a valid CSV ({exc}).") from exc
    except OSError as exc:
        log.exception("Could not open %s", path)
        raise DataError(f"{filename} could not be opened: {exc}") from exc

    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise DataError(f"{filename} is missing required columns: {', '.join(missing)}.")
    df = df.apply(lambda col: col.str.strip())
    return coerce_types(df)


def save_table(df: pd.DataFrame, path, filename: str) -> None:
    """Write df to path atomically (temp file in the same folder, then replace)."""
    path = Path(path)
    tmp_name = None
    try:
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}_", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            df.to_csv(handle, index=False, na_rep="", float_format="%.10g")
        os.replace(tmp_name, path)
    except (PermissionError, OSError) as exc:
        log.exception("Could not write %s", path)
        if tmp_name and os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass
        raise DataError(f"Could not save {filename}: {exc}. Is the file open in another program?") from exc
