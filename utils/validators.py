"""Shared validation helpers.

Every check_* function returns an error message (str) or None when the value is fine.
Blank values count as "missing" and are only an error when required=True.
"""
import math
from datetime import date, datetime

SEVERITIES = ["Fatal", "Serious", "Minor", "Unknown"]
VISIBILITY = ["Good", "Moderate", "Poor"]
WEATHER = ["Clear", "Cloudy", "Rain", "Fog", "Storm", "Unknown"]
ROAD_CONDITIONS = ["Dry", "Wet", "Damaged", "Waterlogged", "Unknown"]
LIGHTING = ["Daylight", "Dusk", "Night-Lit", "Night-Unlit", "Unknown"]
ROAD_TYPES = ["National Highway", "State Highway", "City Road", "Rural Road", "Unknown"]
TRAFFIC_DENSITY = ["Low", "Medium", "High"]
VEHICLE_TYPES = ["Two-wheeler", "Car", "Auto-rickshaw", "Bus", "Truck", "Other", "Unknown"]

MAX_SPEED_LIMIT_KMH = 200

# Documented mapping from raw source wording to RoadSafe severity (see README).
_SEVERITY_MAP = {
    "fatal": "Fatal", "fatal injury": "Fatal", "killed": "Fatal", "death": "Fatal", "1": "Fatal",
    "serious": "Serious", "serious injury": "Serious", "severe": "Serious", "grievous": "Serious",
    "grievous injury": "Serious", "2": "Serious",
    "minor": "Minor", "slight": "Minor", "slight injury": "Minor", "simple": "Minor",
    "simple injury": "Minor", "3": "Minor",
}


def is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    try:  # pandas NA
        import pandas as pd
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() == ""


def normalize_severity(value) -> str:
    """Map source wording to Fatal / Serious / Minor / Unknown. Unmapped values -> Unknown."""
    if is_blank(value):
        return "Unknown"
    return _SEVERITY_MAP.get(str(value).strip().lower(), "Unknown")


def check_id(value, label: str):
    if is_blank(value):
        return f"{label} is required."
    if len(str(value).strip()) > 50:
        return f"{label} must be 50 characters or fewer."
    return None


def check_date(value, label: str = "Date", required: bool = True):
    if is_blank(value):
        return f"{label} is required." if required else None
    try:
        parsed = datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return f"{label} must be a real date in YYYY-MM-DD format."
    if parsed > date.today():
        return f"{label} cannot be in the future."
    return None


def check_time(value, label: str = "Time"):
    if is_blank(value):
        return None
    try:
        datetime.strptime(str(value).strip(), "%H:%M")
    except ValueError:
        return f"{label} must be in HH:MM (24-hour) format."
    return None


def _to_float(value):
    try:
        number = float(str(value).strip())
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def check_coordinate(value, label: str, low: float, high: float):
    if is_blank(value):
        return None
    number = _to_float(value)
    if number is None:
        return f"{label} must be a number."
    if not low <= number <= high:
        return f"{label} must be between {low:g} and {high:g}."
    return None


def check_coordinate_pair(lat, lon):
    """Return a list of errors for a latitude/longitude pair (both or neither)."""
    errors = [
        check_coordinate(lat, "Latitude", -90, 90),
        check_coordinate(lon, "Longitude", -180, 180),
    ]
    if is_blank(lat) != is_blank(lon):
        errors.append("Provide both Latitude and Longitude, or leave both blank.")
    return [e for e in errors if e]


def check_count(value, label: str, required: bool = False, minimum: int = 0):
    if is_blank(value):
        return f"{label} is required." if required else None
    number = _to_float(value)
    if number is None or number != int(number):
        return f"{label} must be a whole number."
    if number < minimum:
        return f"{label} must be {minimum} or more."
    return None


def check_speed_limit(value):
    if is_blank(value):
        return None
    number = _to_float(value)
    if number is None:
        return "Speed_Limit must be a number (km/h)."
    if not 0 < number <= MAX_SPEED_LIMIT_KMH:
        return f"Speed_Limit must be above 0 and at most {MAX_SPEED_LIMIT_KMH} km/h."
    return None


def check_bool_like(value, label: str = "Is_Synthetic"):
    if is_blank(value) or str(value).strip().lower() not in ("true", "false"):
        return f"{label} must be 'true' or 'false'."
    return None


def check_required_text(value, label: str):
    return f"{label} is required." if is_blank(value) else None
