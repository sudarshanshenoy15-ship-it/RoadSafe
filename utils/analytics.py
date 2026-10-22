"""Reusable summary calculations and the rule-based risk score.

All functions take DataFrames loaded by the managers and return DataFrames/dicts,
so they can be tested without Streamlit.
"""
import pandas as pd

# ---------------------------------------------------------------- filtering
def is_synthetic(df: pd.DataFrame) -> pd.Series:
    return df["Is_Synthetic"].astype(str).str.lower().eq("true")


def filter_accidents(acc: pd.DataFrame, start=None, end=None, severities=None, source="All") -> pd.DataFrame:
    """Filter by date range (ISO strings or dates), severity list and source ('All'/'Public'/'Synthetic')."""
    out = acc
    if start is not None and end is not None:
        dates = pd.to_datetime(out["Date"], errors="coerce")
        out = out[(dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))]
    if severities:
        from utils.validators import normalize_severity
        normalized = out["Severity"].map(normalize_severity)
        out = out[normalized.isin(severities)]
    if source == "Public":
        out = out[~is_synthetic(out)]
    elif source == "Synthetic":
        out = out[is_synthetic(out)]
    return out


def filter_by_accidents(df: pd.DataFrame, accident_ids) -> pd.DataFrame:
    return df[df["Accident_ID"].isin(set(accident_ids))]


# ---------------------------------------------------------------- basics
def valid_coordinate_mask(df: pd.DataFrame) -> pd.Series:
    lat, lon = df["Latitude"], df["Longitude"]
    return lat.between(-90, 90) & lon.between(-180, 180)


def summary_metrics(acc: pd.DataFrame) -> dict:
    total = int(acc["Accident_ID"].nunique())
    casualties = acc["Number_of_Casualties"]
    with_coords = int(valid_coordinate_mask(acc).sum())
    synth = int(is_synthetic(acc).sum())
    return {
        "total_accidents": total,
        "total_casualties": int(casualties.sum()) if casualties.notna().any() else None,
        "casualties_missing": int(casualties.isna().sum()),
        "with_coordinates": with_coords,
        "coordinate_pct": round(100 * with_coords / total, 1) if total else 0.0,
        "synthetic": synth,
        "public": len(acc) - synth,
    }


def _counts(series: pd.Series, name: str, label: str = "Count") -> pd.DataFrame:
    out = series.value_counts().rename_axis(name).reset_index()
    out.columns = [name, label]
    return out


def severity_counts(acc: pd.DataFrame) -> pd.DataFrame:
    """Count source severities after normalizing their wording to RoadSafe categories."""
    from utils.validators import normalize_severity
    normalized = acc["Severity"].map(normalize_severity)
    out = _counts(normalized, "Severity", "Accidents")
    order = ["Fatal", "Serious", "Minor", "Unknown"]
    out["Severity"] = pd.Categorical(out["Severity"], categories=order, ordered=True)
    return out.sort_values("Severity").reset_index(drop=True)


def severity_options(acc: pd.DataFrame) -> list:
    """Return normalized severity filter choices, including categories present in the data."""
    from utils.validators import normalize_severity
    present = {normalize_severity(value) for value in acc["Severity"].dropna()}
    return [value for value in ["Fatal", "Serious", "Minor", "Unknown"] if value in present]


def monthly_counts(acc: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(acc["Date"], errors="coerce").dropna()
    if dates.empty:
        return pd.DataFrame(columns=["Month", "Accidents"])
    out = dates.dt.strftime("%Y-%m").value_counts().sort_index().rename_axis("Month").reset_index()
    out.columns = ["Month", "Accidents"]
    return out


def vehicle_type_counts(veh: pd.DataFrame) -> pd.DataFrame:
    """Vehicles by type = sum of Vehicle_Count (each row is a group of vehicles of one type)."""
    known = veh.dropna(subset=["Vehicle_Count"])
    if known.empty:
        return pd.DataFrame(columns=["Vehicle_Type", "Vehicles"])
    out = known.groupby("Vehicle_Type")["Vehicle_Count"].sum().astype(int)
    return out.sort_values(ascending=False).rename("Vehicles").reset_index()


def speed_limit_counts(veh: pd.DataFrame) -> pd.DataFrame:
    known = veh.dropna(subset=["Speed_Limit"])
    if known.empty:
        return pd.DataFrame(columns=["Speed_Limit", "Records"])
    out = known["Speed_Limit"].value_counts().sort_index().rename_axis("Speed_Limit").reset_index()
    out.columns = ["Speed_Limit", "Records"]
    return out


def road_condition_counts(loc: pd.DataFrame) -> pd.DataFrame:
    known = loc[loc["Road_Condition"].ne("") & loc["Road_Condition"].ne("Unknown")]
    return _counts(known["Road_Condition"], "Road_Condition", "Records") if len(known) else \
        pd.DataFrame(columns=["Road_Condition", "Records"])


def weather_casualty_summary(cond: pd.DataFrame) -> pd.DataFrame:
    known = cond[cond["Weather"].ne("") & cond["Weather"].ne("Unknown")]
    if known.empty:
        return pd.DataFrame(columns=["Weather", "Records", "Casualties", "Fatalities", "Injuries"])
    # min_count=1 prevents an all-missing group from being misleadingly shown as zero.
    grouped = known.groupby("Weather").agg(
        Records=("Record_ID", "count"),
        Casualties=("Casualties", lambda values: values.sum(min_count=1)),
        Fatalities=("Fatalities", lambda values: values.sum(min_count=1)),
        Injuries=("Injuries", lambda values: values.sum(min_count=1)),
    )
    return grouped.reset_index().sort_values("Records", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- risk score
RISK_WEIGHTS = {
    "Severity": 30, "Fatalities": 20, "Injuries": 15,
    "Weather": 15, "Road condition": 10, "Lighting": 10,
}
SEVERITY_POINTS = {"Fatal": 1.0, "Serious": 0.6, "Minor": 0.2}
WEATHER_POINTS = {"Clear": 0.0, "Cloudy": 0.25, "Rain": 0.6, "Fog": 0.9, "Storm": 1.0}
ROAD_POINTS = {"Dry": 0.0, "Wet": 0.6, "Damaged": 0.8, "Waterlogged": 1.0}
LIGHTING_POINTS = {"Daylight": 0.0, "Dusk": 0.4, "Night-Lit": 0.6, "Night-Unlit": 1.0}
FATALITY_CAP = 3   # 3 or more fatalities = full fatality points
INJURY_CAP = 5     # 5 or more injuries = full injury points

RISK_FORMULA_TEXT = (
    "Score = 30 x Severity + 20 x Fatalities + 15 x Injuries + 15 x Weather + 10 x Road condition + 10 x Lighting "
    "(each factor scaled 0-1, total 0-100)."
)
RISK_LIMITATIONS = [
    "This is a project-defined descriptive indicator of how severe an accident record and its recorded conditions look. "
    "It is not a validated model and does not predict future accidents.",
    "Weights and category points are chosen by the project team, not estimated from data.",
    "Severity, fatalities and injuries describe the outcome of the accident, so the score reflects outcome as well as conditions.",
    "Descriptive charts do not show cause and effect.",
    "If any of the six inputs is missing or has an unrecognised value, the score is not calculated (shown as 'Insufficient data').",
]


def _is_missing(value) -> bool:
    return value is None or (not isinstance(value, str) and pd.isna(value))


def _normalize_risk_categories(severity, weather, road_condition, lighting):
    """Normalize known source-dataset labels without changing the raw CSV values."""
    from utils.validators import normalize_severity
    sev = normalize_severity(severity)
    weather_map = {
        "normal": "Clear", "clear": "Clear", "cloudy": "Cloudy", "overcast": "Cloudy",
        "raining": "Rain", "rain": "Rain", "light rain": "Rain", "foggy": "Fog", "fog": "Fog",
        "windy": "Storm", "storm": "Storm", "unknown": "Unknown",
    }
    road_map = {
        "dry": "Dry", "wet": "Wet", "wet or damp": "Wet", "damp": "Wet",
        "flood over 3cm": "Waterlogged", "waterlogged": "Waterlogged", "damaged": "Damaged",
        "unknown": "Unknown",
    }
    light_map = {
        "daylight": "Daylight", "darkness - lights lit": "Night-Lit",
        "darkness - lights unlit": "Night-Unlit", "darkness - no lighting": "Night-Unlit",
        "darkness - lights lit and unlit": "Night-Unlit", "dusk": "Dusk",
        "street-lit night": "Night-Lit", "night-lit": "Night-Lit", "night-unlit": "Night-Unlit",
        "unknown": "Unknown",
    }
    return (sev, weather_map.get(str(weather).strip().lower(), weather),
            road_map.get(str(road_condition).strip().lower(), road_condition),
            light_map.get(str(lighting).strip().lower(), lighting))


def compute_risk_score(severity, fatalities, injuries, weather, road_condition, lighting):
    """Return a 0-100 score (float, 1 decimal) or None when any input is missing/unrecognised."""
    if any(_is_missing(x) for x in (severity, fatalities, injuries, weather, road_condition, lighting)):
        return None
    severity, weather, road_condition, lighting = _normalize_risk_categories(
        severity, weather, road_condition, lighting
    )
    try:
        fatalities, injuries = float(fatalities), float(injuries)
    except (TypeError, ValueError):
        return None
    if fatalities < 0 or injuries < 0:
        return None
    if (severity not in SEVERITY_POINTS or weather not in WEATHER_POINTS
            or road_condition not in ROAD_POINTS or lighting not in LIGHTING_POINTS):
        return None
    score = (
        RISK_WEIGHTS["Severity"] * SEVERITY_POINTS[severity]
        + RISK_WEIGHTS["Fatalities"] * min(fatalities, FATALITY_CAP) / FATALITY_CAP
        + RISK_WEIGHTS["Injuries"] * min(injuries, INJURY_CAP) / INJURY_CAP
        + RISK_WEIGHTS["Weather"] * WEATHER_POINTS[weather]
        + RISK_WEIGHTS["Road condition"] * ROAD_POINTS[road_condition]
        + RISK_WEIGHTS["Lighting"] * LIGHTING_POINTS[lighting]
    )
    return round(score, 1)


def risk_band(score) -> str:
    if score is None or pd.isna(score):
        return "Insufficient data"
    if score >= 67:
        return "High"
    if score >= 34:
        return "Medium"
    return "Low"


def build_risk_table(acc: pd.DataFrame, loc: pd.DataFrame, cond: pd.DataFrame) -> pd.DataFrame:
    """One row per accident with its inputs, score (NaN if insufficient) and band."""
    base = acc[["Accident_ID", "Severity"]].drop_duplicates("Accident_ID")
    loc1 = loc[["Accident_ID", "Road_Condition", "Lighting_Condition"]].drop_duplicates("Accident_ID")
    cond1 = cond[["Accident_ID", "Weather", "Fatalities", "Injuries"]].drop_duplicates("Accident_ID")
    table = base.merge(loc1, on="Accident_ID", how="left").merge(cond1, on="Accident_ID", how="left")
    scores = [
        compute_risk_score(r.Severity, r.Fatalities, r.Injuries, r.Weather, r.Road_Condition, r.Lighting_Condition)
        for r in table.itertuples(index=False)
    ]
    table["Risk_Score"] = pd.Series(scores, dtype="float64")
    table["Risk_Band"] = table["Risk_Score"].map(risk_band)
    return table
