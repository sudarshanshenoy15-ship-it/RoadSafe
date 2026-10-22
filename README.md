# RoadSafe: Road Accident Hotspot and Safety Analytics

A Streamlit app that manages road-accident records in four linked CSV files and shows descriptive
analytics: tables, Plotly charts, a general hotspot map, a rule-based 0-100 risk score and downloadable
reports. Aligned with UN SDG 11 (Sustainable Cities and Communities).

> **Data status: mixed source-backed and synthetic demo data.** The four bundled CSVs each contain 50 records transformed from the uploaded Kaggle Road Traffic Accident dataset (Addis Ababa, Ethiopia) plus 10 clearly labelled synthetic records. The synthetic map points are illustrative Kerala coordinates, not observed accidents. See `data/raw/SOURCES.md` before interpreting results.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Run tests: `python -m pytest`
Build a standalone synthetic-only dataset (30 accidents) elsewhere: `python scripts/generate_sample_data.py --out some_folder`. The script refuses to overwrite existing CSVs unless `--force` is given, because the bundled `data/sample` files contain real source-backed rows that it cannot recreate.
Use another data folder: set the `ROADSAFE_DATA_DIR` environment variable.

## Pages

| Page | What it does |
|---|---|
| Dashboard | Accident count, known casualties, coordinate coverage, public/synthetic split, severity chart, monthly trend |
| Accidents | Table, search, filters, add / edit / delete (delete needs a confirm tick; linked rows are removed with it) |
| Vehicles | Vehicle table and CRUD, vehicles-by-type chart, speed-limit chart (km/h) |
| Locations & Hotspots | Plotly map (points or grid counts), road-condition chart, location CRUD |
| Risk Analysis | Casualties by weather, risk-score distribution, formula and limitations, weather/casualty CRUD |
| Reports | Text report, CSV summary and filtered-accidents CSV, each with timestamp and active filters |

All pages share the sidebar filters (date range, severity, source). Public and synthetic rows are always distinguishable.

## Project layout

```
app.py                      entry point
pages/                      six Streamlit pages (UI only)
managers/                   AccidentManager, VehicleManager, LocationManager, RiskManager (+ small base_manager.py)
utils/                      paths, data_loader, validators, analytics, hotspot_detection, report_generator, ui
scripts/generate_sample_data.py   builds a standalone synthetic-only dataset (fixed seed, never overwrites by default)
data/sample/                the four CSVs the app reads (50 source-backed + 10 synthetic rows each)
data/raw, data/processed    empty, reserved for public data
tests/                      pytest suite
docs/SPECIFICATION.md       original specification
```

`utils/ui.py` (shared Streamlit helpers) and `managers/base_manager.py` (shared CRUD code) are small additions beyond the
spec's file list, to avoid repeating the same code four to six times.

## Decisions taken (spec section 18)

- **Schemas:** exactly as in the specification. Linking key is `Accident_ID`; one location row and one conditions row per accident, one or more vehicle rows.
- **Severity:** `Fatal / Serious / Minor / Unknown`. Blank becomes `Unknown`. For future source data, `normalize_severity()` maps
  fatal/killed/1 -> Fatal; serious/severe/grievous/2 -> Serious; minor/slight/simple/3 -> Minor; anything else -> Unknown (never guessed).
  The numeric codes are a placeholder convention and must be checked against the real source before use.
- **Units:** speed limit in km/h; visibility `Good / Moderate / Poor` (blank = not recorded).
- **Category lists:** Weather Clear/Cloudy/Rain/Fog/Storm; Road condition Dry/Wet/Damaged/Waterlogged; Lighting Daylight/Dusk/Night-Lit/Night-Unlit; plus `Unknown`. Input is matched case-insensitively.
- **Counts:** `Number_of_Vehicles` is the accident-level total. `Vehicle_Count` on a vehicle row is how many vehicles of that type that row represents; the vehicle chart sums it. In the synthetic data the two always agree.
- **Editing source-backed rows:** original source wording (e.g. `Slight Injury`, blank Date, `17:02:00`) is kept as-is. Only fields you actually change are validated against the category/format rules; new records are always validated strictly.
- **Missing values are never treated as zero.** Totals use known values only and report how many are missing.
- **`Risk_Factor`** column: kept for schema compatibility as an optional free note. It is **not** used by the score (avoids circular logic).
- **Deleting an accident** also deletes its linked vehicle/location/conditions rows (the UI says so first). The manager refuses otherwise, so no orphan rows can appear.
- **Date filter:** applies only once narrowed from the full range; rows with no valid date stay in unfiltered views.

## Risk score (0-100, descriptive only)

`Score = 30 x Severity + 20 x Fatalities + 15 x Injuries + 15 x Weather + 10 x Road condition + 10 x Lighting`, each factor scaled 0-1:

| Factor | Scaling |
|---|---|
| Severity | Fatal 1.0, Serious 0.6, Minor 0.2 |
| Fatalities | fatalities / 3, capped at 1 |
| Injuries | injuries / 5, capped at 1 |
| Weather | Clear 0, Cloudy 0.25, Rain 0.6, Fog 0.9, Storm 1.0 |
| Road condition | Dry 0, Wet 0.6, Damaged 0.8, Waterlogged 1.0 |
| Lighting | Daylight 0, Dusk 0.4, Night-Lit 0.6, Night-Unlit 1.0 |

Bands: Low < 34, Medium 34 to 66.9, High >= 67. If any of the six inputs is missing or `Unknown`, the app shows **"Insufficient data"**.
The weights are project choices, not fitted to data. The score is not a prediction, and because severity/fatalities/injuries are outcomes,
it describes how severe a record and its conditions look, not what causes accidents. The same text is shown on the Risk Analysis page.

## Hotspot map

Plots recorded accident coordinates (accident row first, falling back to the location row). Rows with missing or out-of-range coordinates are skipped.
"Grid counts" groups points into fixed square cells (default 0.05 degrees, about 5.5 km tall; selectable) and sizes/colours bubbles by count.
It is a simple count of recorded accidents, not a statistical cluster test and not a risk forecast. No routing or GPS. Map tiles need an internet connection.

## Status

| Feature | Status |
|---|---|
| Four linked CSVs with provenance columns (`Data_Source`, `Is_Synthetic`) | Included: 50 source-backed + 10 synthetic rows per file |
| Safe CSV load/save (temp file + replace), friendly errors for missing/empty/malformed files, missing columns, write failures | Implemented and tested |
| Four managers with add / update / delete, validation, link checks, duplicate checks | Implemented and tested |
| Six Streamlit pages and CRUD flows | Implemented; automated AppTest checks are included in `tests/test_app_smoke.py` |
| Analytics, hotspot grid, risk score, reports | Implemented and tested |
| Source sample, column mapping and provenance (`data/raw/SOURCES.md`) | Included; original uploaded ZIP retained in `data/raw/` |
| PDF report export | Not implemented (optional in spec) |
| Visual check of every page in a real browser | **Not done** by the builder |

## Source data and geographic limitations

- The source-backed rows are transformed from the uploaded **Road Traffic Accident (RTA) Dataset**, available on Kaggle: https://www.kaggle.com/datasets/saurabhshahane/road-traffic-accidents . The source records are associated with Addis Ababa, Ethiopia, not Kerala.
- The source provides no GPS coordinates and no full calendar date. Real-source rows therefore have blank latitude, longitude and date. The map only plots the 10 synthetic demo points; they are explicitly labelled as illustrative.
- The full uploaded source archive is retained as `data/raw/RTA_Dataset_original.zip`; the exact 50-row source sample used for mapping is `data/raw/RTA_Dataset_source_sample.csv`.
- Field mapping, limitations and attribution notes are documented in `data/raw/SOURCES.md`. Check the source page for current license/attribution terms before redistributing the source data.
- Risk analysis normalizes known source labels for display/scoring without changing the raw CSV values. If required score inputs (such as separate fatality/injury counts) are missing, the record remains unscored rather than inferring values.

## Team (planned responsibilities from the project document; first names only)

| Member | Module | Dataset | Class |
|---|---|---|---|
| Sudarshan | Accident records and data management | `accidents.csv` | `AccidentManager` |
| Akhil | Vehicle and traffic analysis | `vehicles.csv` | `VehicleManager` |
| Aravind | Location, road and hotspot analysis | `locations.csv` | `LocationManager` |
| Akshay | Weather, casualty and risk analysis | `conditions_casualties.csv` | `RiskManager` |

These are planned assignments, not a record of completed individual work.

## Known limitations

- Synthetic coordinates are random scatter near Kerala towns; some points may fall on water or off any road.
- Single-user app: no file locking, and simultaneous edits from two sessions are last-write-wins.
- Category lists are fixed; real source values need mapping first.
- Tested on Python 3.12 only (the spec says 3.10+; not verified on 3.10/3.11).
- The standalone generator (`scripts/generate_sample_data.py`) makes 30 synthetic rows with deliberate gaps (2 without coordinates, 1 without time, 1 Unknown severity, 1 Unknown weather, 1 Unknown lighting). The bundled data/sample files use 10 hand-set synthetic rows instead.
