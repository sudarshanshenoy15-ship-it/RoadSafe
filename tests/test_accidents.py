import os

import pandas as pd
import pytest

from managers.accident_manager import AccidentManager
from tests.conftest import accident
from utils.data_loader import DataError, ValidationError, load_table


def test_load_sample(data_dir):
    df = AccidentManager(data_dir).load_data()
    assert len(df) == 30
    assert df["Latitude"].isna().sum() == 2        # blanks stay missing, not zero


def test_add_persists_after_reload(data_dir):
    AccidentManager(data_dir).add_record(accident())
    reloaded = AccidentManager(data_dir).load_data()
    row = reloaded[reloaded["Accident_ID"] == "T-A001"].iloc[0]
    assert row["Date"] == "2025-03-10" and row["Latitude"] == 9.93 and row["Number_of_Vehicles"] == 2
    assert len(reloaded) == 31


def test_duplicate_id_rejected(data_dir):
    m = AccidentManager(data_dir)
    m.add_record(accident())
    with pytest.raises(ValidationError, match="already exists"):
        m.add_record(accident())
    with pytest.raises(ValidationError, match="already exists"):
        m.add_record(accident(Accident_ID="SYN-A001"))


@pytest.mark.parametrize("bad", [
    {"Date": "2025-13-40"}, {"Date": ""}, {"Time": "25:61"}, {"Latitude": "95"}, {"Longitude": "200"},
    {"Latitude": "", "Longitude": "76"}, {"Number_of_Casualties": "-2"}, {"Number_of_Vehicles": "-1"},
    {"Severity": "Catastrophic"}, {"Accident_ID": " "}, {"Is_Synthetic": "maybe"}, {"Data_Source": ""},
])
def test_invalid_records_rejected(data_dir, bad):
    m = AccidentManager(data_dir)
    with pytest.raises(ValidationError):
        m.add_record(accident(**bad))
    assert len(m.load_data()) == 30                # nothing written


def test_blank_severity_becomes_unknown_and_case_is_matched(data_dir):
    m = AccidentManager(data_dir)
    assert m.add_record(accident(Accident_ID="T-1", Severity=""))["Severity"] == "Unknown"
    assert m.add_record(accident(Accident_ID="T-2", Severity="fatal"))["Severity"] == "Fatal"


def test_update(data_dir):
    m = AccidentManager(data_dir)
    m.update_record("SYN-A001", {"Severity": "Minor", "Number_of_Casualties": "0"})
    row = m.get_record("SYN-A001")
    assert row["Severity"] == "Minor" and row["Number_of_Casualties"] == 0
    assert len(m.load_data()) == 30
    with pytest.raises(ValidationError):
        m.update_record("SYN-A001", {"Latitude": "999"})
    with pytest.raises(ValidationError, match="not found"):
        m.update_record("NOPE", {"Severity": "Minor"})


def test_delete_requires_cascade_when_linked(data_dir):
    m = AccidentManager(data_dir)
    with pytest.raises(ValidationError, match="linked"):
        m.delete_record("SYN-A001")
    m.delete_record("SYN-A001", cascade=True)
    assert m.get_record("SYN-A001") is None
    assert m.linked_counts("SYN-A001") == {"vehicles": 0, "locations": 0, "conditions_casualties": 0}


def test_delete_unlinked_and_missing(data_dir):
    m = AccidentManager(data_dir)
    m.add_record(accident())
    m.delete_record("T-A001")
    assert m.get_record("T-A001") is None
    with pytest.raises(ValidationError, match="not found"):
        m.delete_record("T-A001")


def test_missing_file_is_a_friendly_error(tmp_path):
    with pytest.raises(DataError, match="not found"):
        AccidentManager(tmp_path).load_data()


def test_empty_and_header_only_files(tmp_path):
    (tmp_path / "accidents.csv").write_text("")
    assert AccidentManager(tmp_path).load_data().empty
    (tmp_path / "accidents.csv").write_text("Accident_ID,Date\n")
    with pytest.raises(DataError, match="missing required columns"):
        AccidentManager(tmp_path).load_data()


def test_extra_source_columns_preserved(data_dir):
    path = data_dir / "accidents.csv"
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df["District"] = "Ernakulam"
    df.to_csv(path, index=False)
    m = AccidentManager(data_dir)
    m.add_record(accident())
    m.update_record("SYN-A002", {"Severity": "Serious"})
    out = pd.read_csv(path, dtype=str, keep_default_na=False)
    assert "District" in out.columns and (out.loc[out["Accident_ID"] == "SYN-A002", "District"] == "Ernakulam").all()


def test_write_failure_is_handled_and_file_untouched(data_dir, monkeypatch):
    m = AccidentManager(data_dir)
    before = (data_dir / "accidents.csv").read_text()

    def boom(*args, **kwargs):
        raise PermissionError("locked")
    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(DataError, match="Could not save"):
        m.add_record(accident())
    monkeypatch.undo()
    assert (data_dir / "accidents.csv").read_text() == before
    assert not list(data_dir.glob("*.tmp"))        # temp file cleaned up


def test_malformed_csv(tmp_path):
    (tmp_path / "accidents.csv").write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(DataError):
        load_table(tmp_path / "accidents.csv", "accidents.csv")
