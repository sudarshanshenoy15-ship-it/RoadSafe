"""Project-relative paths. Nothing here depends on the terminal's working directory."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
REPORTS_DIR = PROJECT_ROOT / "reports"

ACCIDENTS_FILE = "accidents.csv"
VEHICLES_FILE = "vehicles.csv"
LOCATIONS_FILE = "locations.csv"
CONDITIONS_FILE = "conditions_casualties.csv"


def get_data_dir() -> Path:
    """Folder holding the four CSVs. Override with the ROADSAFE_DATA_DIR env variable."""
    override = os.environ.get("ROADSAFE_DATA_DIR")
    return Path(override) if override else SAMPLE_DIR
