import pytest

from managers.location_manager import LocationManager
from utils.data_loader import ValidationError


def location(**o):
    base = {"Location_ID": "T-L1", "Accident_ID": "SYN-A001", "Latitude": "9.9", "Longitude": "76.2",
            "Road_Type": "City Road", "Road_Condition": "Dry", "Lighting_Condition": "Daylight",
            "Traffic_Density": "Low", "Data_Source": "test", "Is_Synthetic": "true"}
    base.update(o)
    return base


def test_add_and_categories_normalized(data_dir):
    m = LocationManager(data_dir)
    m.add_record(location(Road_Condition="wet", Road_Type=""))
    rec = m.get_record("T-L1")
    assert rec["Road_Condition"] == "Wet" and rec["Road_Type"] == "Unknown"


@pytest.mark.parametrize("bad", [{"Latitude": "100"}, {"Longitude": "-181"}, {"Latitude": ""},
                                 {"Road_Condition": "Icy"}, {"Accident_ID": "NOPE"}, {"Location_ID": "SYN-L001"}])
def test_invalid_location_rejected(data_dir, bad):
    with pytest.raises(ValidationError):
        LocationManager(data_dir).add_record(location(**bad))


def test_update_and_delete(data_dir):
    m = LocationManager(data_dir)
    m.update_record("SYN-L001", {"Road_Condition": "Damaged"})
    assert m.get_record("SYN-L001")["Road_Condition"] == "Damaged"
    m.delete_record("SYN-L001")
    assert m.get_record("SYN-L001") is None
