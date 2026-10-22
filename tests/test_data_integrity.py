import pandas as pd

from managers.accident_manager import AccidentManager
from managers.location_manager import LocationManager
from managers.risk_manager import RiskManager
from managers.vehicle_manager import VehicleManager
from scripts.generate_sample_data import generate
from utils.data_loader import SCHEMAS
from utils.paths import SAMPLE_DIR


def load_all(d):
    return (AccidentManager(d).load_data(), VehicleManager(d).load_data(),
            LocationManager(d).load_data(), RiskManager(d).load_data())


def test_shipped_sample_csvs_include_required_schema_columns():
    # Source-derived CSVs may retain extra provenance/source fields; required app columns must exist.
    for name, cols in SCHEMAS.items():
        actual = list(pd.read_csv(SAMPLE_DIR / name, nrows=0).columns)
        assert set(cols) <= set(actual)


def test_unique_ids_and_valid_links():
    acc, veh, loc, cond = load_all(SAMPLE_DIR)
    for df, col in ((acc, "Accident_ID"), (veh, "Vehicle_ID"), (loc, "Location_ID"), (cond, "Record_ID")):
        assert df[col].is_unique and (df[col] != "").all()
    ids = set(acc["Accident_ID"])
    for df in (veh, loc, cond):
        assert set(df["Accident_ID"]) <= ids
    assert loc["Accident_ID"].is_unique and cond["Accident_ID"].is_unique      # one row per accident
    assert set(veh["Accident_ID"]) == ids                                      # every accident has vehicles


def test_source_and_synthetic_rows_are_explicitly_labelled():
    for df in load_all(SAMPLE_DIR):
        assert set(df["Is_Synthetic"].unique()) == {"true", "false"}
        assert df["Data_Source"].notna().all() and (df["Data_Source"] != "").all()
    acc = load_all(SAMPLE_DIR)[0]
    assert (acc[acc["Is_Synthetic"] == "false"]["Accident_ID"].str.startswith("RTA-")).all()
    assert (acc[acc["Is_Synthetic"] == "true"]["Accident_ID"].str.startswith("SYN-")).all()
    assert int((acc["Is_Synthetic"] == "false").sum()) == 50
    assert int((acc["Is_Synthetic"] == "true").sum()) == 10


def test_synthetic_counts_are_consistent_and_source_missingness_is_preserved():
    acc, veh, loc, cond = load_all(SAMPLE_DIR)
    merged = acc[acc["Is_Synthetic"] == "true"].merge(cond, on="Accident_ID")
    assert (merged["Casualties"] == merged["Fatalities"] + merged["Injuries"]).all()
    assert (merged["Number_of_Casualties"] == merged["Casualties"]).all()
    totals = veh[veh["Is_Synthetic"] == "true"].groupby("Accident_ID")["Vehicle_Count"].sum()
    synth_acc = acc[acc["Is_Synthetic"] == "true"].set_index("Accident_ID")
    assert (synth_acc["Number_of_Vehicles"] == totals).all()
    for col in ("Casualties", "Fatalities", "Injuries"):
        assert (cond[cond["Is_Synthetic"] == "true"][col] >= 0).all()
    # Source has total casualties, but no separate fatality/injury totals or GPS coordinates.
    source_cond = cond[cond["Is_Synthetic"] == "false"]
    source_acc = acc[acc["Is_Synthetic"] == "false"]
    assert source_cond["Fatalities"].isna().all() and source_cond["Injuries"].isna().all()
    assert source_acc["Latitude"].isna().all() and source_acc["Longitude"].isna().all()


def test_coordinates_valid_and_in_kerala_box():
    acc, _, loc, _ = load_all(SAMPLE_DIR)
    for df in (acc, loc):
        known = df.dropna(subset=["Latitude", "Longitude"])
        assert known["Latitude"].between(8, 12.5).all() and known["Longitude"].between(74.5, 77.5).all()
    source = acc[acc["Is_Synthetic"] == "false"]
    assert source["Latitude"].isna().all() and source["Longitude"].isna().all()
    demo = acc[acc["Is_Synthetic"] == "true"]
    assert demo["Latitude"].notna().sum() == len(demo)


def test_sample_generator_still_creates_consistent_synthetic_demo_data():
    generated = generate()
    for name, df in generated.items():
        assert (df["Is_Synthetic"] == "true").all(), name
        assert (df["Data_Source"] == "synthetic_sample").all(), name
    assert len(generated["accidents.csv"]) == 30
    assert len(generated["locations.csv"]) == 30
    assert len(generated["conditions_casualties.csv"]) == 30


def test_visibility_and_speed_units_use_documented_values():
    _, veh, _, cond = load_all(SAMPLE_DIR)
    assert set(cond[cond["Is_Synthetic"] == "true"]["Visibility"]) <= {"Good", "Moderate", "Poor"}
    assert veh[veh["Is_Synthetic"] == "true"]["Speed_Limit"].dropna().between(20, 120).all()


def test_source_categories_are_normalized_for_analytics_without_rewriting_csv_values():
    from utils.analytics import severity_counts, filter_accidents, compute_risk_score
    acc = load_all(SAMPLE_DIR)[0]
    assert "Slight Injury" in set(acc[acc["Is_Synthetic"] == "false"]["Severity"])
    counts = severity_counts(acc).set_index("Severity")["Accidents"].to_dict()
    assert sum(counts.values()) == len(acc)
    assert len(filter_accidents(acc, severities=["Minor"])) > 0
    # The source's missing separate fatality/injury counts are not inferred.
    assert compute_risk_score("Slight Injury", None, None, "Normal", "Dry", "Daylight") is None
