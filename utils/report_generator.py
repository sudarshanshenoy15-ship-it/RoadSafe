"""Build downloadable CSV and plain-text reports from the currently filtered data."""
import io
from datetime import datetime

import pandas as pd

from utils import analytics as an
from utils.hotspot_detection import DEFAULT_CELL_SIZE_DEG, accident_points, grid_counts

SECTIONS = ["Accidents", "Vehicles", "Locations", "Risk"]


def _fmt_filters(filters: dict) -> list:
    return [f"{k}: {v}" for k, v in filters.items()]


def _section_rows(section, acc, veh, loc, cond):
    """Return list of (metric, value) tuples for a section."""
    rows = []
    if section == "Accidents":
        m = an.summary_metrics(acc)
        rows += [("Accidents", m["total_accidents"]),
                 ("Total casualties (known values)", m["total_casualties"] if m["total_casualties"] is not None else "n/a"),
                 ("Accidents with missing casualty count", m["casualties_missing"]),
                 ("Accidents with valid coordinates", f'{m["with_coordinates"]} ({m["coordinate_pct"]}%)')]
        rows += [(f"Severity: {r.Severity}", r.Accidents) for r in an.severity_counts(acc).itertuples()]
    elif section == "Vehicles":
        rows.append(("Vehicle records", len(veh)))
        rows += [(f"Vehicles: {r.Vehicle_Type}", r.Vehicles) for r in an.vehicle_type_counts(veh).itertuples()]
        speeds = veh["Speed_Limit"].dropna()
        rows.append(("Speed limit (km/h), median", float(speeds.median()) if len(speeds) else "n/a"))
        rows.append(("Vehicle records without speed limit", int(veh["Speed_Limit"].isna().sum())))
    elif section == "Locations":
        pts = accident_points(acc, loc)
        grid = grid_counts(pts)
        rows.append(("Location records", len(loc)))
        rows.append(("Mapped accidents", len(pts)))
        if len(grid):
            top = grid.iloc[0]
            rows.append((f"Busiest grid cell ({DEFAULT_CELL_SIZE_DEG} deg), centre",
                         f"{top.Cell_Lat}, {top.Cell_Lon}: {int(top.Accidents)} accidents"))
        rows += [(f"Road condition: {r.Road_Condition}", r.Records) for r in an.road_condition_counts(loc).itertuples()]
    elif section == "Risk":
        table = an.build_risk_table(acc, loc, cond)
        scored = table["Risk_Score"].dropna()
        rows.append(("Accidents with a risk score", len(scored)))
        rows.append(("Accidents with insufficient data", int(table["Risk_Score"].isna().sum())))
        if len(scored):
            rows.append(("Average risk score", round(float(scored.mean()), 1)))
        rows += [(f"Weather {r.Weather}: casualties", r.Casualties) for r in an.weather_casualty_summary(cond).itertuples()]
    return rows


def _key_findings(acc, cond):
    findings = []
    if acc.empty:
        return ["No accident records match the active filters."]
    sev = an.severity_counts(acc)
    sev = sev[sev["Accidents"] > 0]
    top = sev.sort_values("Accidents", ascending=False).iloc[0]
    findings.append(f"The most common recorded severity is {top.Severity} ({int(top.Accidents)} of {len(acc)} accidents).")
    months = an.monthly_counts(acc)
    if len(months):
        best = months.sort_values("Accidents", ascending=False).iloc[0]
        findings.append(f"The month with the most recorded accidents is {best.Month} ({int(best.Accidents)}).")
    weather = an.weather_casualty_summary(cond)
    if len(weather):
        w = weather.sort_values("Casualties", ascending=False).iloc[0]
        findings.append(f"Weather category with the highest recorded casualty total: {w.Weather} ({int(w.Casualties)}); "
                        "this is descriptive and does not show cause.")
    return findings


def build_summary_rows(filters, acc, veh, loc, cond, sections, now=None) -> pd.DataFrame:
    now = now or datetime.now()
    rows = [("Report", "Generated", now.strftime("%Y-%m-%d %H:%M:%S"))]
    rows += [("Filter", k, v) for k, v in filters.items()]
    rows += [("Scope", "Synthetic records included", int(an.is_synthetic(acc).sum())),
             ("Scope", "Public records included", int((~an.is_synthetic(acc)).sum())),
             ("Scope", "Unique accidents", int(acc["Accident_ID"].nunique()))]
    for section in sections:
        rows += [(section, metric, value) for metric, value in _section_rows(section, acc, veh, loc, cond)]
    return pd.DataFrame(rows, columns=["Section", "Metric", "Value"])


def build_csv_report(filters, acc, veh, loc, cond, sections, now=None) -> str:
    buffer = io.StringIO()
    build_summary_rows(filters, acc, veh, loc, cond, sections, now).to_csv(buffer, index=False)
    return buffer.getvalue()


def build_text_report(filters, acc, veh, loc, cond, sections, now=None) -> str:
    now = now or datetime.now()
    synth = int(an.is_synthetic(acc).sum())
    lines = ["ROADSAFE SUMMARY REPORT", f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}", "", "ACTIVE FILTERS"]
    lines += [f"  {f}" for f in _fmt_filters(filters)] or ["  (none)"]
    lines += ["", "DATA SCOPE",
              f"  Accident rows: {len(acc)} (unique accidents: {acc['Accident_ID'].nunique()})",
              f"  Vehicle rows: {len(veh)} | Location rows: {len(loc)} | Conditions rows: {len(cond)}",
              f"  Source mix: {len(acc) - synth} public, {synth} synthetic"]
    if len(acc) and synth == len(acc):
        lines.append("  NOTE: all records are synthetic demonstration data, not real accidents.")
    for section in sections:
        lines += ["", section.upper()]
        lines += [f"  {metric}: {value}" for metric, value in _section_rows(section, acc, veh, loc, cond)]
    lines += ["", "KEY FINDINGS"] + [f"  - {f}" for f in _key_findings(acc, cond)]
    lines += ["", "CAVEATS",
              "  - Missing values are reported separately and are not treated as zero.",
              "  - Hotspot counts show recorded accidents only, not future risk.",
              "  - The risk score is a project-defined descriptive indicator, not a prediction."]
    return "\n".join(lines) + "\n"
