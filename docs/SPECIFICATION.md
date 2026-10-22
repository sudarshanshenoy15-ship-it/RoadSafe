# RoadSafe — Road Accident Hotspot & Safety Analytics

> **Purpose:** This document is the primary implementation specification and handoff guide for RoadSafe. A developer or AI coding agent should be able to use it to build, run, test, and extend the project without needing undocumented decisions.
>
> **Project status:** Specification and initial build plan. The original project document describes intended features; it does not prove that any implementation is already complete. Mark a feature as complete only after it has been implemented and tested.

## 1. Project summary

RoadSafe is a Python web application built with Streamlit. It manages road-accident records and presents descriptive road-safety analytics through tables, charts, and a general geographical hotspot map.

The system is intended to:
- Manage accident records and related vehicle, location, weather, and casualty information.
- Support Create, Read, Update, and Delete (CRUD) operations for each dataset.
- Validate input and handle missing, malformed, and duplicate data safely.
- Summarize accident patterns by severity, time, vehicle type, road condition, weather, and casualty outcomes.
- Display accident concentrations on a **general map**, not a route-navigation or live-GPS map.
- Calculate a transparent, rule-based risk score from 0 to 100.
- Export summary reports.
- Demonstrate Python, object-oriented programming (OOP), CSV file handling, Pandas, NumPy, Streamlit, Plotly, validation, exception handling, and testing.

The project aligns with **UN Sustainable Development Goal 11: Sustainable Cities and Communities**.

### 1.1 Scope: keep it achievable

Build a working, clear college project. Prefer simple functions and classes over unnecessary architecture.

**In scope**
- Streamlit multi-page UI with a minimal design.
- Four CSV datasets.
- Four manager classes.
- CRUD, validation, summary statistics, Plotly charts, a general hotspot map, a simple explainable risk score, and report export.
- Basic automated tests and clear setup instructions.

**Out of scope for the initial version**
- Live GPS tracking, route planning, route-based warnings, turn-by-turn navigation, live traffic, user accounts, cloud deployment, machine-learning accident prediction, complex GIS infrastructure, or an external database.
- Do not add SQLite: CSV is the initial source of truth.
- Do not claim that the risk score predicts future accidents or establishes causation.

## 2. Team and contribution plan

The following names and assignments are from the supplied `RoadSafe_Project_Documentation-1.docx`. It lists first names only.

| Member | Assigned module | Dataset | Class | Planned contribution |
|---|---|---|---|---|
| Sudarshan | Accident records and data management | `accidents.csv` | `AccidentManager` | Accident CRUD, validation, accident summaries, severity and time charts, accident report |
| Akhil | Vehicle and traffic analysis | `vehicles.csv` | `VehicleManager` | Vehicle CRUD, vehicle validation, vehicle-type and speed-limit analysis, traffic charts and report |
| Aravind | Location, road and hotspot analysis | `locations.csv` | `LocationManager` | Location CRUD, coordinate/road validation, hotspot map and road-condition analysis/report |
| Akshay | Weather, casualty and risk analysis | `conditions_casualties.csv` | `RiskManager` | Weather/casualty CRUD, validation, casualty and risk analysis, risk score and report |

These are **planned/documented responsibilities**, not verified records of completed individual work. Do not invent surnames, student IDs, or additional contributions. Update this table if the team confirms changes.

### 2.1 Shared responsibilities
- Agree on shared ID conventions and CSV schemas before implementing modules.
- Keep each manager responsible for its own dataset.
- Reuse shared validation and data-loading helpers instead of duplicating code.
- Integrate pages through common data-loading and analytics utilities.
- Review changes that affect shared schemas or `Accident_ID` links.

## 3. Technology stack

- Python 3.10 or newer (use a compatible version consistently).
- Streamlit for the web UI.
- Pandas for CSV loading, validation, filtering, grouping, and summaries.
- NumPy for numerical calculations where useful.
- Plotly Express for charts and a map/geo visualization.
- `pytest` for tests.
- CSV files as the primary data store.
- Git/GitHub may be used for version control.

Keep the dependency list small. Pin compatible minimum versions in `requirements.txt` after verifying the build environment. Avoid adding libraries unless the project genuinely needs them.

## 4. Proposed directory structure

This is the intended structure. If an existing repository is supplied later, inspect it and reconcile it with this specification rather than blindly overwriting files.

```text
RoadSafe/
├── app.py
├── pages/
│   ├── 1_Dashboard.py
│   ├── 2_Accidents.py
│   ├── 3_Vehicles.py
│   ├── 4_Locations_Hotspots.py
│   ├── 5_Risk_Analysis.py
│   └── 6_Reports.py
├── managers/
│   ├── __init__.py
│   ├── accident_manager.py
│   ├── vehicle_manager.py
│   ├── location_manager.py
│   └── risk_manager.py
├── utils/
│   ├── __init__.py
│   ├── paths.py
│   ├── data_loader.py
│   ├── validators.py
│   ├── analytics.py
│   ├── hotspot_detection.py
│   └── report_generator.py
├── data/
│   ├── raw/                 # Original downloaded source files; never silently overwrite
│   ├── processed/           # Cleaned public data, if needed
│   └── sample/              # Clearly labelled synthetic/sample records
│       ├── accidents.csv
│       ├── vehicles.csv
│       ├── locations.csv
│       └── conditions_casualties.csv
├── reports/                 # Exported reports; generated at runtime
├── tests/
│   ├── test_accidents.py
│   ├── test_vehicles.py
│   ├── test_locations.py
│   ├── test_risk.py
│   ├── test_validators.py
│   └── test_data_integrity.py
├── requirements.txt
├── .gitignore
└── README.md
```

### 4.1 File responsibilities
- `app.py`: Streamlit entry point, application title, shared navigation/overview and global styling.
- `pages/`: page-level UI only; call manager and utility methods rather than embedding all business logic in page files.
- `managers/`: dataset-specific CRUD and dataset-level operations.
- `utils/paths.py`: resolve project-relative paths reliably; do not depend on the terminal's current working directory.
- `utils/data_loader.py`: read CSVs, verify expected columns, provide safe empty-state handling, and write updated CSVs safely.
- `utils/validators.py`: shared validation helpers for IDs, numbers, dates, coordinates, and required values.
- `utils/analytics.py`: reusable summary calculations.
- `utils/hotspot_detection.py`: aggregate recorded accident coordinates into map markers or a simple grid-based concentration view.
- `utils/report_generator.py`: generate downloadable CSV/text summaries.
- `data/raw/`: original public data and source notes.
- `data/processed/`: transformed public records if transformations are necessary.
- `data/sample/`: project-ready CSVs used by the app. Sample rows must be identifiable as sample data.
- `tests/`: unit tests for CRUD, validation, formulas, and data integrity.
- `reports/`: optional local export destination; user downloads should also work through Streamlit download controls.

## 5. Data source strategy

Use a hybrid approach:
1. A public road-safety dataset for genuine recorded information.
2. Our own clearly labelled synthetic/sample records to demonstrate fields and UI behaviour not supported by the public source.

### 5.1 Source selection rules
- Prefer an official source for Indian road-safety statistics and, if possible, a detailed public dataset containing individual accident coordinates.
- Potential starting points to verify:
  - Government of India's Open Government Data platform: https://www.data.gov.in/
  - Kerala Open Government Data portal: https://kerala.data.gov.in/
- These portals may provide aggregate tables rather than individual, geocoded accident records. **Do not assume that a source supports hotspot mapping until its actual fields and granularity have been inspected.**
- Record the dataset title, publisher, exact download URL, access date, licence/usage terms, geographic coverage, date range, fields, and any transformations in `data/raw/SOURCES.md` (create this file when the dataset is selected).
- If a suitable coordinate-level public dataset cannot be found, use an appropriately licensed dataset from another geography for the map demonstration and explain its geographic scope. Do not label non-Indian data as Indian.
- Do not scrape sites in violation of their terms or use private/personal accident records.

### 5.2 Source provenance and mixed records
Each final record must be distinguishable as public-source data or synthetic/sample data. Add these provenance fields to the final CSV schemas:
- `Data_Source`: short source label, such as `public:<dataset-short-name>` or `synthetic_sample`.
- `Is_Synthetic`: boolean-like value `true` or `false`.

For a public source, preserve the original source file unchanged in `data/raw/`. Map its columns into RoadSafe's schemas in a documented transformation. Do not invent missing fields and then present them as observed facts. Where a field is unavailable, use an empty value/unknown category when appropriate, or keep the record out of analyses that require that field.

Synthetic data can be created to demonstrate the full application, but:
- Mark every synthetic row clearly.
- Use obviously fictional identifiers such as `SYN-A001` and coordinates chosen only for demonstration.
- Do not describe synthetic rows as real accidents.
- Avoid merging a synthetic row into a public record unless it genuinely represents the same event, which should not be assumed.
- Keep public and synthetic rows filterable in the UI.

### 5.3 Initial build data
Create small but useful sample CSV files for development and tests so the app runs before the public dataset has been downloaded. Use a modest dataset (for example, 20–50 synthetic accidents and corresponding linked rows) rather than creating a huge dataset. Make the demo status obvious in the UI. Replace or supplement this data when a compatible public dataset is selected and mapped.

## 6. CSV schemas and relationships

These are the planned application schemas. The exact source-to-schema mapping must be documented once a real public dataset is chosen.

### 6.1 `accidents.csv`
One row per accident.

| Column | Type | Rules / meaning |
|---|---|---|
| `Accident_ID` | string | Required, unique, stable ID |
| `Date` | ISO date string `YYYY-MM-DD` | Required if known; validate date |
| `Time` | string `HH:MM` | Optional if unavailable; validate format if provided |
| `Latitude` | float | Optional if unavailable; otherwise range -90 to 90 |
| `Longitude` | float | Optional if unavailable; otherwise range -180 to 180 |
| `Severity` | category | Normalized category; use `Unknown` when not provided, not as a guessed value |
| `Number_of_Casualties` | non-negative integer | Must not be negative; do not assume every source defines this identically |
| `Number_of_Vehicles` | positive/non-negative integer | Validate against the chosen source definition; never silently infer |
| `Data_Source` | string | Provenance label |
| `Is_Synthetic` | boolean-like | `true`/`false` |

### 6.2 `vehicles.csv`
One row per vehicle record associated with an accident.

| Column | Type | Rules / meaning |
|---|---|---|
| `Vehicle_ID` | string | Required, unique |
| `Accident_ID` | string | Required link to `accidents.csv` |
| `Vehicle_Type` | category/string | Required if known; use `Unknown` when unavailable |
| `Vehicle_Count` | non-negative integer | Follow source semantics; avoid double-counting when each row already represents one vehicle |
| `Speed_Limit` | positive number or blank | Unit must be documented; do not infer an unknown limit |
| `Vehicle_Movement` | category/string | Optional if source lacks it |
| `Data_Source` | string | Provenance label |
| `Is_Synthetic` | boolean-like | `true`/`false` |

### 6.3 `locations.csv`
One row per accident location/road context record.

| Column | Type | Rules / meaning |
|---|---|---|
| `Location_ID` | string | Required, unique |
| `Accident_ID` | string | Required link to `accidents.csv` |
| `Latitude` | float | Optional; if present, -90 to 90 |
| `Longitude` | float | Optional; if present, -180 to 180 |
| `Road_Type` | category/string | Use source value or `Unknown` |
| `Road_Condition` | category/string | Use source value or `Unknown` |
| `Lighting_Condition` | category/string | Optional if unavailable |
| `Traffic_Density` | category/string | Optional if unavailable; do not invent observations |
| `Data_Source` | string | Provenance label |
| `Is_Synthetic` | boolean-like | `true`/`false` |

### 6.4 `conditions_casualties.csv`
One row per accident conditions/casualty record.

| Column | Type | Rules / meaning |
|---|---|---|
| `Record_ID` | string | Required, unique |
| `Accident_ID` | string | Required link to `accidents.csv` |
| `Weather` | category/string | Use source value or `Unknown` |
| `Visibility` | category/string or numeric | Choose one representation and document units if numeric |
| `Casualties` | non-negative integer | Align definition with source; may correspond to total casualties |
| `Fatalities` | non-negative integer | Must not be negative |
| `Injuries` | non-negative integer | Must not be negative |
| `Risk_Factor` | numeric/category | Define whether this is an input factor or derived output; avoid circular scoring |
| `Data_Source` | string | Provenance label |
| `Is_Synthetic` | boolean-like | `true`/`false` |

### 6.5 Integrity rules
- `Accident_ID` is the linking key across all four datasets.
- Every non-empty `Accident_ID` in related files must exist in `accidents.csv`.
- IDs must be unique within their own table.
- A single accident may link to multiple vehicle records, but its location and conditions rows should follow a documented one-to-one or one-to-many rule. Prefer one location and one conditions/casualty summary row per accident for the initial version to keep it simple.
- Keep totals consistent where the public source defines them consistently. Do not assume `Casualties = Fatalities + Injuries` unless the selected source's definitions support that equation.
- The `Number_of_Vehicles` field is the accident-level total. Do not sum duplicated accident-level values from the vehicle table.
- Missing values are not zero. Treat them separately in analysis.
- Ensure filters can distinguish public and synthetic records.
- Document every schema mapping and unit conversion.

## 7. Application workflow

1. Start Streamlit with `streamlit run app.py`.
2. Load the four project CSV files using project-relative paths.
3. Check file availability and expected columns.
4. Display a clear demo/empty-data state if data is missing; do not crash with a raw traceback.
5. Allow the user to view/filter records and perform CRUD operations.
6. Validate inputs before writing changes.
7. Save updates safely and reload the data for the current view.
8. Compute summaries and charts from the current filtered data.
9. Display geographical accident concentrations only for records with valid coordinates.
10. Generate reports based on current filters and timestamp the export.

### 7.1 Safe CSV writes
- Use UTF-8 encoding.
- Do not overwrite `data/raw/` source files through the app.
- Before saving, write to a temporary file in the same directory and then replace the target file to reduce the chance of corruption.
- Handle `PermissionError`, malformed CSV errors, missing files, and invalid records with clear user-facing messages.
- Avoid silently discarding unrecognized columns from a source dataset.
- Do not create or mutate files at import time; use explicit setup/data-generation commands or documented initialization behaviour.

## 8. Minimal UI specification

### 8.1 Visual style
- Use a clean, restrained light theme by default.
- White/light-grey surfaces, dark readable text, and one restrained accent colour.
- Simple typography and consistent spacing.
- Avoid unnecessary gradients, decorative animations, and excessive cards.
- Keep labels, chart titles, units, and empty states clear.
- Prefer native Streamlit components; do not build a separate JavaScript frontend.

### 8.2 Navigation
Use the Streamlit multipage structure:
- Dashboard
- Accidents
- Vehicles
- Locations & Hotspots
- Risk Analysis
- Reports

### 8.3 Dashboard
Show a compact set of metrics:
- Total recorded accidents
- Total casualties (only where definitions and data availability support the metric)
- Severity distribution
- Records with valid coordinates
- Public vs synthetic record counts

Include a simple time trend and severity chart. All counts must respect selected filters and clearly state when the data is sample-only or incomplete.

### 8.4 Accident management
- Display accident rows in a table.
- Provide search and filters for date range, severity, and source type.
- Provide an add form.
- Provide edit selection by `Accident_ID`.
- Require confirmation before deletion.
- Validate ID uniqueness, date/time formats, coordinate ranges, and numeric values.
- Show success/error feedback after a confirmed operation.

### 8.5 Vehicle analysis
- Display vehicle records and filters.
- Support add, edit, and confirmed delete.
- Check that the linked `Accident_ID` exists.
- Show vehicle type counts and speed-limit distribution only when values are available and meaningful.
- Explain the unit used for speed limits.

### 8.6 Locations and general hotspot map
This is a **general historical hotspot map**, not route navigation.
- Plot valid accident coordinates using Plotly.
- Provide a heatmap or aggregated marker view where supported by the available data.
- Allow filtering by geographic region when region fields exist, severity, date range, and public/sample source.
- Include a simple road-condition chart.
- Do not plot rows with missing or invalid coordinates.
- Do not invent GPS coordinates for real accidents.
- If only aggregate district-level statistics are available, show district-level summaries instead of falsely precise point locations.
- Marker colour or heat intensity represents recorded accident concentration, not proven future risk.
- If only synthetic data is loaded, label the map clearly as a demonstration.

For the initial version, use the simplest reliable map implementation supported by the chosen data. Avoid route APIs and live location.

### 8.7 Risk analysis
- Show casualty, fatality, and injury summaries only when fields are available.
- Show casualty distribution by weather and a risk-score distribution.
- Explain the score formula and limitations on the page.
- Do not imply causal relationships from descriptive charts.

### 8.8 Reports
Allow download of:
- CSV summary of filtered records/statistics.
- Plain-text report with generation timestamp, active filters, row counts, summary statistics, data source mix, and key findings.
- PDF export is optional and should be added only if easy to maintain.

## 9. Analytics and calculations

All formulas must be implemented in reusable utility functions and covered by tests.

### 9.1 Basic summaries
- Total accidents: number of unique valid `Accident_ID` values in the filtered accident dataset.
- Total casualties: sum of known non-negative casualty counts only; report the number of missing values.
- Accidents by severity: group counts by normalized severity category.
- Accidents over time: group by date or month, depending on dataset size and date coverage.
- Vehicle-type distribution: count vehicle records or vehicles according to the chosen dataset's row semantics; label the metric accurately.
- Road-condition distribution: group known location records by road condition.
- Weather/casualty summary: group known records by weather and show counts/sums with missingness noted.
- Coordinates coverage: number and percentage of accidents with valid latitude and longitude.
- Public/sample split: counts by `Is_Synthetic` and `Data_Source`.

### 9.2 Hotspot method
For the first version, use a straightforward geographic aggregation:
- Exclude missing or invalid coordinates.
- Either plot individual recorded coordinates with transparent markers or aggregate points into simple fixed-size geographic grid cells.
- If grid aggregation is used, document the cell size and label the result as a concentration map.
- Avoid claiming that a cluster is statistically significant without an appropriate statistical method.
- Use recorded accident counts, not an invented prediction score, to represent concentration.
- Test the method with known synthetic coordinates and expected groupings.

### 9.3 Transparent risk score
Use a simple rule-based score for demonstration, not a trained prediction model. The initial implementation may use a documented weighted combination of available indicators, normalized to 0–100. The exact formula and weights must be selected before final scoring code is written, and the UI must show them.

Rules:
- Do not include a field in the formula unless it exists and has a defined meaning.
- Do not silently treat missing values as zero or as the lowest risk.
- Do not calculate the score using `Risk_Factor` if `Risk_Factor` itself is defined from the score (avoid circular logic).
- If the available data is insufficient, show “Insufficient data” rather than a misleading score.
- Clearly state that the score is a project-defined descriptive indicator and is not a validated prediction of future accidents.
- Test boundaries, missing data, and expected score ordering.

## 10. CRUD and class requirements

Each manager class should provide a consistent, simple interface. Example methods (final names may be adjusted consistently):
- `load_data()`
- `get_all()` or equivalent
- `add_record(record)`
- `update_record(record_id, updates)`
- `delete_record(record_id)`
- `validate_record(record)` or call shared validators
- Dataset-specific summary methods where appropriate

### 10.1 `AccidentManager`
Owns `accidents.csv`. Enforce unique `Accident_ID`, valid date/time, coordinate ranges, and non-negative counts.

### 10.2 `VehicleManager`
Owns `vehicles.csv`. Enforce unique `Vehicle_ID`, valid `Accident_ID` references, non-negative counts, and sensible speed-limit values.

### 10.3 `LocationManager`
Owns `locations.csv`. Enforce unique `Location_ID`, valid `Accident_ID` references, coordinate ranges, and normalized category values.

### 10.4 `RiskManager`
Owns `conditions_casualties.csv`. Enforce unique `Record_ID`, valid `Accident_ID` references, non-negative casualty counts, and valid risk inputs.

### 10.5 OOP expectations
- Use encapsulation where it improves clarity.
- Inheritance is optional; do not add an artificial inheritance hierarchy merely to claim that inheritance is used.
- Keep manager methods short and understandable.
- Avoid excessive abstractions, dependency-injection frameworks, or elaborate design patterns.

## 11. Validation and error handling

Handle at least:
- Missing CSV file.
- Empty CSV file.
- Missing expected columns.
- Invalid data types.
- Blank or duplicate IDs.
- Invalid dates and times.
- Coordinates outside valid ranges.
- Negative casualty/vehicle counts.
- Related records referencing an unknown `Accident_ID`.
- CSV parse errors.
- File permission and write errors.
- Empty filter results.
- No valid coordinates for the map.
- Missing data for a chart or risk calculation.

Show clear, actionable messages in the UI. Log useful technical details for debugging without exposing confusing tracebacks to end users. Never swallow exceptions silently.

## 12. Report requirements

Each generated report should include:
- Report title and generation timestamp.
- Active filters.
- Dataset/source scope and whether synthetic rows are included.
- Number of rows and unique accidents used.
- Summary statistics.
- Relevant analytical results.
- Caveats for missing or aggregate-only fields.

Use Streamlit's download controls. CSV and plain text are sufficient for the first version.

## 13. Installation and execution

### 13.1 Prerequisites
- Python 3.10+.
- A terminal.
- A virtual environment is recommended.

### 13.2 Setup
Run these commands from the project root:

```bash
python -m venv .venv
```

Linux/macOS:
```bash
source .venv/bin/activate
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:
```bash
python -m pip install -r requirements.txt
```

Start the app:
```bash
streamlit run app.py
```

The application should display its local URL in the terminal. The exact dependencies and versions must match the implementation.

### 13.3 Expected dependencies
At minimum, evaluate:
- `streamlit`
- `pandas`
- `numpy`
- `plotly`
- `pytest`

Do not add an optional mapping library or PDF library unless the selected implementation requires it. Put all actual runtime and test dependencies in `requirements.txt`.

## 14. Testing and acceptance criteria

The project is not complete merely because the UI launches. Verify all of the following.

### Data and CRUD
- [ ] The app starts when valid sample CSVs exist.
- [ ] The app shows a helpful message if data is missing or empty.
- [ ] A valid accident can be added and persists after reload.
- [ ] Duplicate accident IDs are rejected.
- [ ] A record can be updated.
- [ ] Deletion requires confirmation and removes the selected record.
- [ ] Related vehicle/location/conditions records cannot reference a nonexistent accident.
- [ ] Invalid dates, coordinates, and negative counts are rejected.
- [ ] CSV write errors are handled without crashing the entire app.

### Analytics and UI
- [ ] Dashboard metrics match the underlying filtered data.
- [ ] Charts handle empty or missing data.
- [ ] Public and synthetic records can be distinguished.
- [ ] The map plots only valid recorded coordinates.
- [ ] Aggregate-only sources are not displayed as individual accident points.
- [ ] The risk score follows its documented formula and handles missing inputs honestly.
- [ ] CSV and text report downloads work and include filters/timestamps.

### Project quality
- [ ] The code is split according to the documented structure.
- [ ] The four manager classes have clear responsibilities.
- [ ] Tests pass using `pytest`.
- [ ] Setup instructions work in a clean environment.
- [ ] No secrets, private personal data, or downloaded raw data are accidentally committed.
- [ ] README status distinguishes implemented and unimplemented features.

## 15. Git and generated files

Suggested `.gitignore` entries:

```gitignore
.venv/
__pycache__/
.pytest_cache/
*.py[cod]
.env
reports/*
!reports/.gitkeep
```

Only ignore files that should genuinely be excluded. Decide whether source datasets may be committed based on their licence and size. Never commit credentials or private accident information.

## 16. Development order

Build in this order to keep the project achievable:
1. Create the folder structure, `requirements.txt`, paths helper, and small synthetic CSVs.
2. Implement shared CSV loading and validation.
3. Implement and test `AccidentManager`.
4. Implement and test the other three managers.
5. Build the minimal Streamlit dashboard and CRUD pages.
6. Add summary analytics and charts.
7. Add the general hotspot map using verified coordinates.
8. Select and document the risk-score formula, then implement it with tests.
9. Add CSV/text report downloads.
10. Select, document, and map the public dataset; preserve raw source files and provenance.
11. Run the full test suite and verify setup from a clean environment.
12. Update the completion checklist and known limitations.

## 17. Instructions for an AI coding agent

When using this file to build RoadSafe:

1. Read the entire specification before writing code.
2. Inspect the existing repository first, if one is provided. Do not overwrite useful work without understanding it.
3. Treat the schemas, team assignments, UI scope, and CSV-only storage as the agreed baseline unless the user explicitly updates them.
4. Implement the simplest solution that satisfies the requirements.
5. Create all required source files and sample CSVs; do not provide only snippets or pseudocode.
6. Never fabricate real accident records, source URLs, data licences, or geographic precision. Label synthetic data.
7. Inspect the actual public dataset before mapping fields or promising hotspot functionality.
8. If an external data source is unavailable, keep the app runnable with labelled sample data and document the unresolved source task.
9. Do not claim a test passed unless it was run and its result was observed.
10. Run tests and fix failures before reporting completion.
11. Keep team contribution descriptions faithful to the supplied project document and later user confirmations.
12. If a requirement is genuinely ambiguous, choose the least complex safe option, document the decision, and ask the user only if the ambiguity materially changes the outcome.
13. At the end, report created files, implemented features, commands run, test results, and known limitations.

## 18. Decisions still to finalize

Before calling the implementation complete, confirm or document:
- [ ] The exact public dataset, licence, coverage, and download URL.
- [ ] Whether its granularity supports individual coordinates or only aggregate geography.
- [ ] Final category values and severity normalization.
- [ ] Speed-limit and visibility units.
- [ ] Exact rule-based risk-score formula and weights.
- [ ] Final hotspot aggregation method and grid size, if using a grid.
- [ ] Whether team assignments or contributions have changed.
- [ ] Actual implementation status after code has been built and tested.

Until these are confirmed, the application should remain functional with labelled synthetic sample data, and the unresolved decisions must be disclosed rather than guessed.

---

## 19. Source-document reference

The original project document, `RoadSafe_Project_Documentation-1.docx`, specifies:
- Python and Streamlit.
- Pandas, NumPy, Plotly, CSV storage, and optional SQLite.
- Four team modules and their assigned names/classes/datasets.
- CRUD operations, validation, exception handling, statistics, charts, report generation, and SDG 11 alignment.

This README keeps the original four-module plan while choosing CSV-only storage and a general historical hotspot map to reduce complexity. Where the original document does not define implementation details (such as exact public data source, risk weights, or hotspot algorithm), this specification marks them for verification instead of presenting assumptions as established facts.
