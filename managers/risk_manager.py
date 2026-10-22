"""RiskManager: owns conditions_casualties.csv (weather, visibility, casualty counts)."""
from managers.base_manager import BaseManager
from utils import validators as v


class RiskManager(BaseManager):
    filename = "conditions_casualties.csv"
    id_col = "Record_ID"
    category_fields = {"Weather": v.WEATHER, "Visibility": v.VISIBILITY}
    blank_defaults = {"Weather": "Unknown"}

    def _field_errors(self, rec, unchanged=frozenset()):
        return [
            v.check_count(rec["Casualties"], "Casualties"),
            v.check_count(rec["Fatalities"], "Fatalities"),
            v.check_count(rec["Injuries"], "Injuries"),
        ]
