import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.generate_sample_data import write_sample_data  # noqa: E402


@pytest.fixture
def data_dir(tmp_path):
    """A temporary folder holding a fresh copy of the synthetic sample CSVs."""
    write_sample_data(tmp_path)
    return tmp_path


def accident(**overrides):
    base = {"Accident_ID": "T-A001", "Date": "2025-03-10", "Time": "14:30", "Latitude": "9.93", "Longitude": "76.27",
            "Severity": "Minor", "Number_of_Casualties": "1", "Number_of_Vehicles": "2",
            "Data_Source": "test", "Is_Synthetic": "true"}
    base.update(overrides)
    return base
