from datetime import datetime

import pandas as pd

from managers.accident_manager import AccidentManager
from managers.location_manager import LocationManager
from managers.risk_manager import RiskManager
from managers.vehicle_manager import VehicleManager
from utils import analytics as an
from utils.hotspot_detection import accident_points, grid_counts
from utils.report_generator import build_csv_report, build_text_report


def frames(d):
    return (AccidentManager(d).load_data(), VehicleManager(d).load_data(),
            LocationManager(d).load_data(), RiskManager(d).load_data())


def test_summary_metrics_and_missing_not_zero(data_dir):
    acc = frames(data_dir)[0]
    m = an.summary_metrics(acc)
    assert m["total_accidents"] == 30 and m["with_coordinates"] == 28 and m["coordinate_pct"] == 93.3
    assert m["total_casualties"] == int(acc["Number_of_Casualties"].sum())
    acc.loc[0:2, "Number_of_Casualties"] = pd.NA
    m2 = an.summary_metrics(acc)
    assert m2["casualties_missing"] == 3
    assert m2["total_casualties"] == int(acc["Number_of_Casualties"].dropna().sum())
    empty = an.summary_metrics(acc.iloc[0:0])
    assert empty["total_accidents"] == 0 and empty["total_casualties"] is None


def test_filters_match_underlying_data(data_dir):
    acc = frames(data_dir)[0]
    fatal = an.filter_accidents(acc, severities=["Fatal"])
    assert (fatal["Severity"] == "Fatal").all() and len(fatal) == (acc["Severity"] == "Fatal").sum()
    dated = an.filter_accidents(acc, "2025-01-01", "2025-12-31")
    assert dated["Date"].between("2025-01-01", "2025-12-31").all()
    assert an.filter_accidents(acc, source="Public").empty
    assert len(an.filter_accidents(acc, source="Synthetic")) == 30
    assert an.filter_accidents(acc, severities=["Fatal"], source="Public").empty


def test_severity_and_monthly_counts(data_dir):
    acc = frames(data_dir)[0]
    assert an.severity_counts(acc)["Accidents"].sum() == 30
    assert an.monthly_counts(acc)["Accidents"].sum() == 30
    assert an.monthly_counts(acc.iloc[0:0]).empty


def test_vehicle_and_weather_summaries(data_dir):
    _, veh, loc, cond = frames(data_dir)
    assert an.vehicle_type_counts(veh)["Vehicles"].sum() == veh["Vehicle_Count"].sum()
    w = an.weather_casualty_summary(cond)
    assert "Unknown" not in set(w["Weather"])                      # unknown excluded from the chart
    assert w["Records"].sum() == (cond["Weather"] != "Unknown").sum()
    assert an.road_condition_counts(loc.iloc[0:0]).empty
    assert an.vehicle_type_counts(veh.iloc[0:0]).empty


# ---- hotspots ---------------------------------------------------------
def pts(rows):
    return pd.DataFrame(rows, columns=["Latitude", "Longitude", "Severity"])


def test_grid_counts_known_groups():
    p = pts([(9.91, 76.26, "Fatal"), (9.93, 76.27, "Minor"), (9.92, 76.28, "Minor"),   # one cell
             (8.50, 76.94, "Minor")])                                                    # another
    g = grid_counts(p, 0.05)
    assert list(g["Accidents"]) == [3, 1] and list(g["Fatal"]) == [1, 0]
    assert g.iloc[0]["Cell_Lat"] == 9.925 and g.iloc[0]["Cell_Lon"] == 76.275
    assert grid_counts(p.iloc[0:0]).empty


def test_grid_negative_coordinates_do_not_merge_across_zero():
    g = grid_counts(pts([(0.01, 0.01, "Minor"), (-0.01, -0.01, "Minor")]), 0.05)
    assert len(g) == 2


def test_accident_points_excludes_missing_and_invalid_and_uses_fallback(data_dir):
    acc, _, loc, _ = frames(data_dir)
    p = accident_points(acc, loc)
    assert len(p) == 28 and p["Latitude"].between(-90, 90).all()
    bad = acc.copy()
    bad.loc[0, "Latitude"] = 123.0                                   # invalid latitude
    assert "SYN-A001" not in set(accident_points(bad, None)["Accident_ID"])
    gap = acc.copy()
    gap.loc[1, ["Latitude", "Longitude"]] = [float("nan"), float("nan")]
    assert "SYN-A002" in set(accident_points(gap, loc)["Accident_ID"])   # filled from locations.csv


# ---- reports ----------------------------------------------------------
def test_reports_have_filters_timestamp_and_counts(data_dir):
    acc, veh, loc, cond = frames(data_dir)
    fatal = an.filter_accidents(acc, severities=["Fatal"])
    ids = fatal["Accident_ID"]
    args = ({"Severity": "Fatal", "Source": "All"}, fatal, an.filter_by_accidents(veh, ids),
            an.filter_by_accidents(loc, ids), an.filter_by_accidents(cond, ids), ["Accidents", "Vehicles", "Locations", "Risk"])
    now = datetime(2026, 1, 2, 3, 4, 5)
    text = build_text_report(*args, now=now)
    assert "2026-01-02 03:04:05" in text and "Severity: Fatal" in text
    assert f"Accident rows: {len(fatal)}" in text and "all records are synthetic" in text and "KEY FINDINGS" in text
    csv = build_csv_report(*args, now=now)
    assert csv.startswith("Section,Metric,Value") and "2026-01-02 03:04:05" in csv and f"Unique accidents,{len(fatal)}" in csv


def test_report_with_no_rows_does_not_crash(data_dir):
    acc, veh, loc, cond = (f.iloc[0:0] for f in frames(data_dir))
    assert "No accident records" in build_text_report({}, acc, veh, loc, cond, ["Accidents", "Vehicles", "Locations", "Risk"])
    assert build_csv_report({}, acc, veh, loc, cond, ["Accidents", "Risk"])
