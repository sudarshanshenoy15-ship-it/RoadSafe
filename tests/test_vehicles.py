import pytest

from managers.vehicle_manager import VehicleManager
from utils.data_loader import ValidationError


def vehicle(**o):
    base = {"Vehicle_ID": "T-V1", "Accident_ID": "SYN-A001", "Vehicle_Type": "Car", "Vehicle_Count": "1",
            "Speed_Limit": "50", "Vehicle_Movement": "Straight", "Data_Source": "test", "Is_Synthetic": "true"}
    base.update(o)
    return base


def test_add_update_delete(data_dir):
    m = VehicleManager(data_dir)
    n = len(m.load_data())
    m.add_record(vehicle())
    assert len(m.load_data()) == n + 1
    m.update_record("T-V1", {"Speed_Limit": "60"})
    assert m.get_record("T-V1")["Speed_Limit"] == 60.0
    m.delete_record("T-V1")
    assert m.get_record("T-V1") is None


def test_unknown_accident_rejected(data_dir):
    with pytest.raises(ValidationError, match="does not exist"):
        VehicleManager(data_dir).add_record(vehicle(Accident_ID="NOPE"))


@pytest.mark.parametrize("bad", [{"Vehicle_Count": "-1"}, {"Speed_Limit": "0"}, {"Speed_Limit": "abc"},
                                 {"Vehicle_Type": "Spaceship"}, {"Vehicle_ID": ""}, {"Vehicle_ID": "SYN-V001"}])
def test_invalid_vehicle_rejected(data_dir, bad):
    with pytest.raises(ValidationError):
        VehicleManager(data_dir).add_record(vehicle(**bad))


def test_blank_speed_limit_stays_missing_and_type_defaults(data_dir):
    m = VehicleManager(data_dir)
    m.add_record(vehicle(Speed_Limit="", Vehicle_Type=""))
    rec = m.get_record("T-V1")
    assert rec["Speed_Limit"] is None and rec["Vehicle_Type"] == "Unknown"
