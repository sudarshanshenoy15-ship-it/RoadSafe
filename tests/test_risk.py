import pytest

from managers.accident_manager import AccidentManager
from managers.location_manager import LocationManager
from managers.risk_manager import RiskManager
from utils import analytics as an
from utils.data_loader import ValidationError


def cond(**o):
    base = {"Record_ID": "T-R1", "Accident_ID": "SYN-A001", "Weather": "Rain", "Visibility": "Poor", "Casualties": "2",
            "Fatalities": "1", "Injuries": "1", "Risk_Factor": "", "Data_Source": "test", "Is_Synthetic": "true"}
    base.update(o)
    return base


# ---- manager --------------------------------------------------------
def test_manager_crud(data_dir):
    m = RiskManager(data_dir)
    m.add_record(cond())
    m.update_record("T-R1", {"Injuries": "3"})
    assert m.get_record("T-R1")["Injuries"] == 3
    m.delete_record("T-R1")
    assert m.get_record("T-R1") is None


@pytest.mark.parametrize("bad", [{"Fatalities": "-1"}, {"Injuries": "x"}, {"Weather": "Hail"},
                                 {"Visibility": "Terrible"}, {"Accident_ID": "NOPE"}, {"Record_ID": "SYN-R001"}])
def test_invalid_condition_rejected(data_dir, bad):
    with pytest.raises(ValidationError):
        RiskManager(data_dir).add_record(cond(**bad))


# ---- score ----------------------------------------------------------
MAX = dict(severity="Fatal", fatalities=3, injuries=5, weather="Storm", road_condition="Waterlogged", lighting="Night-Unlit")
MIN = dict(severity="Minor", fatalities=0, injuries=0, weather="Clear", road_condition="Dry", lighting="Daylight")


def test_score_bounds():
    assert an.compute_risk_score(**MAX) == 100.0
    assert an.compute_risk_score(**MIN) == 6.0           # only Minor severity contributes: 30 * 0.2
    assert sum(an.RISK_WEIGHTS.values()) == 100


def test_score_caps_at_100_for_large_counts():
    assert an.compute_risk_score(**{**MAX, "fatalities": 50, "injuries": 90}) == 100.0


def test_score_exact_example():
    # Serious(0.6*30=18) + 1 fatality(20/3=6.667) + 2 injuries(15*0.4=6) + Rain(9) + Wet(6) + Dusk(4) = 49.667
    s = an.compute_risk_score("Serious", 1, 2, "Rain", "Wet", "Dusk")
    assert s == 49.7


def test_score_ordering():
    worse = an.compute_risk_score(**{**MIN, "weather": "Fog"})
    assert worse > an.compute_risk_score(**MIN)
    assert an.compute_risk_score(**{**MIN, "severity": "Fatal"}) > an.compute_risk_score(**{**MIN, "severity": "Serious"}) \
        > an.compute_risk_score(**MIN)
    assert an.compute_risk_score(**{**MIN, "lighting": "Night-Unlit"}) > an.compute_risk_score(**{**MIN, "lighting": "Night-Lit"})


@pytest.mark.parametrize("field,value", [("severity", "Unknown"), ("severity", None), ("fatalities", None),
                                         ("injuries", float("nan")), ("weather", "Unknown"), ("weather", ""),
                                         ("road_condition", "Unknown"), ("lighting", "Unknown"),
                                         ("lighting", None), ("fatalities", -1), ("weather", "Hail")])
def test_missing_or_unrecognised_gives_none_not_zero(field, value):
    assert an.compute_risk_score(**{**MAX, field: value}) is None


def test_bands():
    assert an.risk_band(None) == "Insufficient data"
    assert an.risk_band(10) == "Low" and an.risk_band(34) == "Medium" and an.risk_band(66.9) == "Medium"
    assert an.risk_band(67) == "High"


def test_risk_table_marks_incomplete_rows_insufficient(data_dir):
    acc = AccidentManager(data_dir).load_data()
    table = an.build_risk_table(acc, LocationManager(data_dir).load_data(), RiskManager(data_dir).load_data())
    assert len(table) == 30
    insufficient = set(table.loc[table["Risk_Score"].isna(), "Accident_ID"])
    assert insufficient == {"SYN-A015", "SYN-A023", "SYN-A027"}     # unknown lighting / severity / weather
    assert (table.loc[table["Risk_Score"].isna(), "Risk_Band"] == "Insufficient data").all()
    assert table["Risk_Score"].dropna().between(0, 100).all()


def test_accident_without_linked_rows_is_insufficient(data_dir):
    am = AccidentManager(data_dir)
    am.add_record({"Accident_ID": "T-A9", "Date": "2025-01-01", "Severity": "Fatal", "Data_Source": "t", "Is_Synthetic": "true"})
    table = an.build_risk_table(am.load_data(), LocationManager(data_dir).load_data(), RiskManager(data_dir).load_data())
    assert table.loc[table["Accident_ID"] == "T-A9", "Risk_Score"].isna().all()
