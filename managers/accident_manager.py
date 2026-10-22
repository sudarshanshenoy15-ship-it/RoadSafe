"""AccidentManager: owns accidents.csv."""
from managers.base_manager import BaseManager
from managers.location_manager import LocationManager
from managers.risk_manager import RiskManager
from managers.vehicle_manager import VehicleManager
from utils import validators as v
from utils.analytics import summary_metrics
from utils.data_loader import ValidationError


class AccidentManager(BaseManager):
    filename = "accidents.csv"
    id_col = "Accident_ID"
    links_to_accident = False
    category_fields = {"Severity": v.SEVERITIES}
    blank_defaults = {"Severity": "Unknown"}

    def _field_errors(self, rec, unchanged=frozenset()):
        errors = [
            None if "Date" in unchanged else v.check_date(rec["Date"]),
            None if "Time" in unchanged else v.check_time(rec["Time"]),
            v.check_count(rec["Number_of_Casualties"], "Number_of_Casualties"),
            v.check_count(rec["Number_of_Vehicles"], "Number_of_Vehicles"),
        ]
        errors += v.check_coordinate_pair(rec["Latitude"], rec["Longitude"])
        return errors

    def _linked_managers(self):
        return [VehicleManager(self.data_dir), LocationManager(self.data_dir), RiskManager(self.data_dir)]

    def linked_counts(self, accident_id) -> dict:
        names = ["vehicles", "locations", "conditions_casualties"]
        return {n: m.count_for_accident(accident_id) for n, m in zip(names, self._linked_managers())}

    def delete_record(self, record_id, cascade: bool = False) -> None:
        """Delete an accident. Linked rows must be deleted too (cascade=True) or the call is refused."""
        linked = sum(self.linked_counts(record_id).values())
        if linked and not cascade:
            raise ValidationError(
                f"Accident '{record_id}' has {linked} linked record(s). "
                "Delete them first or confirm cascade deletion."
            )
        if self.get_record(record_id) is None:
            raise ValidationError(f"Accident_ID '{record_id}' was not found.")
        for manager in self._linked_managers():
            manager.delete_by_accident(record_id)
        super().delete_record(record_id)

    def summary(self, df=None) -> dict:
        return summary_metrics(self.load_data() if df is None else df)
