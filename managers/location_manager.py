"""LocationManager: owns locations.csv."""
from managers.base_manager import BaseManager
from utils import validators as v


class LocationManager(BaseManager):
    filename = "locations.csv"
    id_col = "Location_ID"
    category_fields = {
        "Road_Type": v.ROAD_TYPES,
        "Road_Condition": v.ROAD_CONDITIONS,
        "Lighting_Condition": v.LIGHTING,
        "Traffic_Density": v.TRAFFIC_DENSITY,
    }
    blank_defaults = {"Road_Type": "Unknown", "Road_Condition": "Unknown"}

    def _field_errors(self, rec, unchanged=frozenset()):
        return v.check_coordinate_pair(rec["Latitude"], rec["Longitude"])
