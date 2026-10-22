# RoadSafe dataset provenance

## Actual source data
- Dataset: **Road Traffic Accident (RTA) Dataset**
- Kaggle page: https://www.kaggle.com/datasets/saurabhshahane/road-traffic-accidents
- Original data is associated with road traffic accident records from Addis Ababa, Ethiopia (2017–2020); it is **not Kerala/India data**.
- This package uses the first 50 records from the uploaded `RTA Dataset.csv` as the source-backed sample. The original columns for those 50 rows are preserved in `data/raw/RTA_Dataset_source_sample.csv`.
- `Data_Source=Kaggle:RTA_Dataset.csv` and `Is_Synthetic=false` identify transformed rows sourced from the uploaded dataset.

## Generated demonstration data
- Ten extra demonstration accidents are generated to make the sample larger and to provide coordinate-bearing examples for the map.
- These rows have `Data_Source=synthetic_demo_data` and `Is_Synthetic=true`.
- The ten generated map points are illustrative coordinates around Kerala, not real accident locations. Do not report them as observed incidents.
- Related vehicle, location, and condition rows for these ten accidents are synthetic too.

## Important limitations and mapping decisions
- The Kaggle source does not provide GPS latitude/longitude in the supplied columns. Coordinates for source-backed records are deliberately blank; no coordinates were invented for real records.
- The source provides `Time` and `Day_of_week`, but no full calendar date, so `Date` is blank for source-backed records.
- `vehicles.csv` contains one **summary row per accident**, carrying the source's `Type_of_vehicle` and `Number_of_vehicles_involved`. It does not claim every vehicle in a multi-vehicle crash was the listed type.
- `locations.csv` stores source-provided area category, road alignment, road surface condition and lighting; exact GPS location and traffic density are not available in the source and remain blank.
- `conditions_casualties.csv` carries source-provided weather, total casualties, casualty severity and cause. Separate fatality/injury totals and visibility are not provided for the source-backed rows and remain blank. Do not infer fatality/injury counts from the accident severity label.
- Blank values mean “not supplied by the source,” not zero.
- These CSVs are a small educational sample, not a complete or geographically representative dataset. Check Kaggle's current dataset page for its current license and attribution requirements before redistribution.

## Application normalization
- The application normalizes source severity labels such as `Fatal injury`, `Serious Injury`, and `Slight Injury` into RoadSafe's Fatal/Serious/Minor categories for charts and filtering. Original source text remains unchanged in the CSVs.
- Weather, lighting, and road-condition labels are mapped only within the rule-based risk calculation where a documented equivalent exists; raw CSV values are retained. Missing fatality/injury counts are not inferred, so those source rows generally remain “Insufficient data” for the six-input risk score.
