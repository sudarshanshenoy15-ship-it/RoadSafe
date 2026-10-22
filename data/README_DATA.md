# RoadSafe CSV sample data

This package contains four linked CSV files, each with **60 rows**:
- `data/sample/accidents.csv`
- `data/sample/vehicles.csv`
- `data/sample/locations.csv`
- `data/sample/conditions_casualties.csv`

The sample contains 50 records transformed from the user-uploaded Kaggle RTA dataset and 10 generated demonstration records. All files use `Accident_ID` to connect related rows. Check `data/raw/SOURCES.md` before analysis.

## Provenance flags
- `Is_Synthetic=false`, `Data_Source=Kaggle:RTA_Dataset.csv`: source-backed record.
- `Is_Synthetic=true`, `Data_Source=synthetic_demo_data`: generated demo record, not a real accident.

## Notes for the app
- Real source records have blank latitude/longitude because the source CSV has no GPS coordinates.
- Only synthetic demo records have coordinates, solely to demonstrate plotting on the map. Filter the map to `Is_Synthetic=true` or show an explicit demo-data label; do not mix those pins into a map presented as real incident locations.
- Empty cells indicate unavailable source information; they do not mean zero.
- `vehicles.csv` is a summary per accident, not a row for each individual vehicle.
- `Date` is blank for the source-backed rows because the dataset has time and weekday but no full calendar date.

See `data/raw/SOURCES.md` for attribution and field-level mapping details.
