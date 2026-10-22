"""Regression tests: source-backed rows stay editable, data is never silently overwritten,
and weekday labels agree with dates."""
import shutil

import pandas as pd
import pytest

from managers.accident_manager import AccidentManager
from managers.location_manager import LocationManager
from managers.risk_manager import RiskManager
from managers.vehicle_manager import VehicleManager
from scripts.generate_sample_data import write_sample_data
from utils.data_loader import ValidationError
from utils.paths import SAMPLE_DIR


@pytest.fixture
def real_dir(tmp_path):
    """A copy of the bundled data (50 source-backed + 10 synthetic rows per file)."""
    shutil.copytree(SAMPLE_DIR, tmp_path / "d")
    return tmp_path / "d"


ROWS = [(AccidentManager, "RTA-0001"), (LocationManager, "RTA-0001-L"),
        (RiskManager, "RTA-0001-C"), (VehicleManager, "RTA-0001-V-SUMMARY")]


@pytest.mark.parametrize("manager_cls,record_id", ROWS)
def test_source_row_can_be_saved_unchanged(real_dir, manager_cls, record_id):
    m = manager_cls(real_dir)
    before = m.get_record(record_id)
    m.update_record(record_id, {})
    assert m.get_record(record_id) == before          # raw source wording preserved


def test_editing_one_field_keeps_other_source_values(real_dir):
    m = AccidentManager(real_dir)
    m.update_record("RTA-0001", {"Number_of_Casualties": "3"})
    rec = m.get_record("RTA-0001")
    assert rec["Number_of_Casualties"] == 3
    assert rec["Severity"] == "Slight Injury" and rec["Date"] in ("", None) and str(rec["Time"]) == "17:02:00"


def test_changed_fields_are_still_validated(real_dir):
    m = AccidentManager(real_dir)
    with pytest.raises(ValidationError):
        m.update_record("RTA-0001", {"Severity": "Bogus"})
    with pytest.raises(ValidationError):
        m.update_record("RTA-0001", {"Date": "not-a-date"})
    with pytest.raises(ValidationError):
        m.update_record("RTA-0001", {"Time": "25:99"})


def test_new_records_remain_strict(real_dir):
    with pytest.raises(ValidationError):
        AccidentManager(real_dir).add_record({"Accident_ID": "X-1", "Severity": "Slight Injury",
                                              "Data_Source": "t", "Is_Synthetic": "true"})


def test_generator_refuses_to_overwrite_existing_data(real_dir):
    with pytest.raises(FileExistsError):
        write_sample_data(real_dir)
    assert len(AccidentManager(real_dir).load_data()) == 60       # untouched
    write_sample_data(real_dir, force=True)                        # explicit opt-in still works
    assert len(AccidentManager(real_dir).load_data()) == 30


def test_weekday_matches_date_in_bundled_data():
    acc = pd.read_csv(SAMPLE_DIR / "accidents.csv", dtype=str, keep_default_na=False)
    dated = acc[acc["Date"] != ""]
    assert (pd.to_datetime(dated["Date"]).dt.day_name() == dated["Day_of_Week"]).all()
