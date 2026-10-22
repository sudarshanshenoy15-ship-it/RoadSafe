"""Generate the labelled SYNTHETIC demo CSVs.

Usage:  python scripts/generate_sample_data.py [--out DIR] [--force]

This builds a standalone, synthetic-only set of 30 accidents. It is NOT how the bundled
data/sample files were made (those hold 50 source-backed Kaggle rows plus 10 synthetic rows),
so it refuses to overwrite existing CSVs unless --force is given.

Every row is fake: IDs start with SYN-, Is_Synthetic is 'true' and Data_Source is
'synthetic_sample'. Coordinates are scattered around Kerala towns for map demonstration
only; they are not real accident locations. Output is deterministic (fixed seed).
"""
import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data_loader import SCHEMAS, save_table  # noqa: E402
from utils.paths import SAMPLE_DIR  # noqa: E402

SOURCE, N_ACCIDENTS = "synthetic_sample", 30
# (town, lat, lon, weight): demonstration cluster centres only
TOWNS = [("Kochi", 9.93, 76.27, 8), ("Thiruvananthapuram", 8.52, 76.94, 6), ("Kozhikode", 11.25, 75.78, 4),
         ("Thrissur", 10.52, 76.21, 4), ("Kollam", 8.89, 76.61, 3), ("Alappuzha", 9.49, 76.33, 3),
         ("Kannur", 11.87, 75.37, 2)]
VEHICLES = ["Two-wheeler", "Car", "Auto-rickshaw", "Bus", "Truck"]
VEHICLE_W = [8, 6, 3, 2, 2]
SPEEDS = {"City Road": [30, 40, 50], "Rural Road": [40, 50], "State Highway": [60, 70], "National Highway": [70, 80]}
MOVEMENTS = ["Straight", "Turning", "Overtaking", "Stationary"]


def _lighting(hour: int, rnd: random.Random) -> str:
    if 7 <= hour < 18:
        return "Daylight"
    if hour in (6, 18, 19):
        return "Dusk"
    return rnd.choice(["Night-Lit", "Night-Unlit"])


def generate() -> dict:
    rnd = random.Random(42)
    towns, weights = TOWNS, [t[3] for t in TOWNS]
    acc, veh, loc, cond = [], [], [], []
    v_no = 1
    for i in range(1, N_ACCIDENTS + 1):
        aid = f"SYN-A{i:03d}"
        day = date(2024, 1, 1) + timedelta(days=rnd.randrange(0, 730))
        hour, minute = rnd.randrange(0, 24), rnd.randrange(0, 60)
        monsoon = day.month in (6, 7, 8, 9)
        weather = rnd.choices(["Clear", "Cloudy", "Rain", "Fog", "Storm"],
                              [2, 2, 8, 1, 2] if monsoon else [8, 4, 2, 1, 0])[0]
        road_cond = rnd.choices(["Dry", "Wet", "Damaged", "Waterlogged"],
                                [1, 6, 2, 2] if weather in ("Rain", "Storm") else [8, 1, 2, 0])[0]
        visibility = {"Fog": "Poor", "Storm": "Poor", "Rain": "Moderate"}.get(weather, "Good")
        road_type = rnd.choice(list(SPEEDS))
        town = rnd.choices(towns, weights)[0]
        lat = round(town[1] + rnd.uniform(-0.04, 0.04), 5)
        lon = round(town[2] + rnd.uniform(-0.04, 0.04), 5)
        # outcome: fatal / serious / minor, consistent counts
        kind = rnd.choices(["Fatal", "Serious", "Minor"], [3, 9, 18])[0]
        fatalities = rnd.choice([1, 1, 1, 2, 3]) if kind == "Fatal" else 0
        injuries = (rnd.randrange(0, 4) if kind == "Fatal" else rnd.randrange(2, 6) if kind == "Serious"
                    else rnd.randrange(0, 2))
        # vehicles (1-3 rows per accident); accident-level total = sum of Vehicle_Count
        total_vehicles = 0
        for _ in range(rnd.choice([1, 2, 2, 3])):
            count = rnd.choice([1, 1, 1, 2])
            total_vehicles += count
            veh.append({
                "Vehicle_ID": f"SYN-V{v_no:03d}", "Accident_ID": aid,
                "Vehicle_Type": rnd.choices(VEHICLES, VEHICLE_W)[0], "Vehicle_Count": count,
                "Speed_Limit": rnd.choice(SPEEDS[road_type]), "Vehicle_Movement": rnd.choice(MOVEMENTS),
                "Data_Source": SOURCE, "Is_Synthetic": "true"})
            v_no += 1
        has_coords, has_time = i not in (7, 19), i != 12
        severity, lighting = kind, _lighting(hour, rnd)
        # a few deliberately incomplete rows so the app shows missing-data handling
        if i == 23:
            severity = "Unknown"
        if i == 27:
            weather = "Unknown"
        if i == 15:
            lighting = "Unknown"
        acc.append({
            "Accident_ID": aid, "Date": day.isoformat(), "Time": f"{hour:02d}:{minute:02d}" if has_time else "",
            "Latitude": lat if has_coords else "", "Longitude": lon if has_coords else "", "Severity": severity,
            "Number_of_Casualties": fatalities + injuries, "Number_of_Vehicles": total_vehicles,
            "Data_Source": SOURCE, "Is_Synthetic": "true"})
        loc.append({
            "Location_ID": f"SYN-L{i:03d}", "Accident_ID": aid,
            "Latitude": lat if has_coords else "", "Longitude": lon if has_coords else "",
            "Road_Type": road_type, "Road_Condition": road_cond, "Lighting_Condition": lighting,
            "Traffic_Density": rnd.choice(["Low", "Medium", "High"]),
            "Data_Source": SOURCE, "Is_Synthetic": "true"})
        cond.append({
            "Record_ID": f"SYN-R{i:03d}", "Accident_ID": aid, "Weather": weather, "Visibility": visibility,
            "Casualties": fatalities + injuries, "Fatalities": fatalities, "Injuries": injuries,
            "Risk_Factor": "", "Data_Source": SOURCE, "Is_Synthetic": "true"})
    frames = {"accidents.csv": acc, "vehicles.csv": veh, "locations.csv": loc, "conditions_casualties.csv": cond}
    return {name: pd.DataFrame(rows, columns=SCHEMAS[name]) for name, rows in frames.items()}


def write_sample_data(out_dir, force: bool = False) -> None:
    """Write the synthetic CSVs. Refuses to replace existing files unless force=True."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = [name for name in SCHEMAS if (out_dir / name).exists()]
    if existing and not force:
        raise FileExistsError(
            f"Refusing to overwrite existing data in {out_dir}: {', '.join(existing)}. "
            "Use --force only if you really want to replace it with synthetic-only data."
        )
    for name, df in generate().items():
        save_table(df, out_dir / name, name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(SAMPLE_DIR), help="output folder (default: data/sample)")
    parser.add_argument("--force", action="store_true", help="overwrite existing CSVs (destroys real rows)")
    args = parser.parse_args()
    try:
        write_sample_data(args.out, force=args.force)
    except FileExistsError as exc:
        sys.exit(str(exc))
    print(f"Synthetic sample CSVs written to {args.out}")
