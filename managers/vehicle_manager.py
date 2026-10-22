"""VehicleManager: owns vehicles.csv."""
from managers.base_manager import BaseManager
from utils import validators as v


class VehicleManager(BaseManager):
    filename = "vehicles.csv"
    id_col = "Vehicle_ID"
    category_fields = {"Vehicle_Type": v.VEHICLE_TYPES}
    blank_defaults = {"Vehicle_Type": "Unknown"}

    def _field_errors(self, rec, unchanged=frozenset()):
        return [
            v.check_count(rec["Vehicle_Count"], "Vehicle_Count"),
            v.check_speed_limit(rec["Speed_Limit"]),
        ]
