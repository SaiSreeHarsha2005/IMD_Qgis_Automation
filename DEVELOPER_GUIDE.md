# DEVELOPER GUIDE: Automated Spatial Data Processing and Thematic Map Generation in QGIS using Python
**Meteorological Centre Hyderabad — India Meteorological Department (IMD)**  
*Ministry of Earth Sciences (MoES), Government of India*

---

## 1. Document Control & Developer Overview

* **Project Title:** Automated Spatial Data Processing and Thematic Map Generation in QGIS using Python
* **Institutional Context:** Meteorological Centre Hyderabad, India Meteorological Department (IMD)
* **Architecture Pattern:** Zero-CSV Direct In-Memory Excel Ingestion & PyQGIS Headless Layout Rendering
* **Python Runtime:** Python 3.12+ (Bundled with standalone QGIS LTR)
* **GIS Engine:** QGIS 3.x LTR (`qgis.core`, `qgis.analysis`, `PyQt5`)
* **Project Developers:**
  * **Minnekanti Sai Sree Harsha** (Project Lead & Core Backend Engineer)
  * **S Nyneeta Rao** (Co-Developer & Cartographic Layout Design)
  * *Academic Institution:* Department of Computer Science & Engineering, Geethanjali College of Engineering and Technology, Hyderabad

---

## 2. Directory Tree & Component Architecture

```
IMD_AUTOMATION_FINALL/
├── config.py                     # Global configuration, auto-detectors, and path resolvers
├── serve_dashboard.py            # Multi-threaded HTTP backend with REST APIs & clean routing
├── open_dashboard.bat            # Windows launcher for dashboard server & default browser
├── run_imd_automation.bat        # Command-line QGIS batch execution launcher
├── deploy_linux.sh               # Headless Ubuntu deployment script (systemd + Xvfb)
├── symbology-style.db            # SQLite symbology database for QGIS styles
│
├── data/
│   ├── input/                    # Raw forecast Excel workbooks (.xlsx)
│   └── shapefiles/               # Canonical 33 Telangana district polygon shapefiles
│       ├── District_Boundary.shp # Shapefile geometry
│       ├── District_Boundary.dbf # Attribute database
│       ├── District_Boundary.prj # Coordinate Reference System (EPSG:4326)
│       └── District_Boundary.shx # Shape index
│
├── scripts/
│   ├── __init__.py
│   ├── imd_automation.py         # Main vector engine and layout orchestrator
│   ├── imd_thunderstorm_warning_layout.py # Symbology layout for thunderstorm warnings
│   └── imd_5day_temp_grid_layout.py       # 3+2 A4 landscape grid summary bulletin renderer
│
├── templates/
│   ├── dashboard.html            # Production telemetry frontend
│   ├── IMD_LOGO.png / .jpeg      # Official cartographic logo assets
│   ├── rain_cloud.svg            # Base precipitation SVG symbol
│   ├── thunderstorm_cloud.svg    # Base convective thunderstorm SVG symbol
│   └── symbols/                  # Official IMD weather icons (SVG & PNG)
│       ├── cloud_light_rain.svg
│       ├── cloud_moderate_rain.svg
│       ├── cloud_heavy_rain.svg
│       ├── cloud_extreme_rain.svg
│       ├── lightning.svg
│       ├── NorthArrow_04.svg
│       ├── thunderstorm.svg
│       ├── thunderstorm_wind.svg
│       ├── wind.svg
│       ├── windsock.svg
│       └── Wind_warning.png
│
├── utils/
│   ├── __init__.py
│   ├── excel_parser.py           # In-memory Excel data extractor & district normalizer
│   ├── atomic_json.py            # Thread-safe atomic JSON read/write routines
│   └── imd_logger.py             # Standardized operational logging framework
│
├── logs/                         # Live runtime logs and run_status.json
│   ├── automation_log.txt        # Full pipeline execution log
│   ├── run_status.json           # Live telemetry state for dashboard polling
│   └── system_health.json        # Health status report
│
└── output/                       # Generated 300 DPI PNG & vector PDF maps
```

---

## 3. Data Ingestion & District Normalization Engine (`utils/excel_parser.py`)

The ingestion module eliminates disk-bound intermediate CSV conversions by reading Excel workbooks directly into Python memory structures using `openpyxl`.

### 3.1 Key Functions

| Function Signature | Description |
| :--- | :--- |
| `parse_multi_hazard_excel_memory(excel_path: str) -> Dict[str, Any]` | Ingests the 7-Day Multi-Hazard forecast sheet into structured dictionaries. Extracts 7-Day spatial coverage, 5-Day thunderstorm warning codes, and 5-Day rainfall intensity codes. Sets `has_intensity_data = True` only if heavy rainfall tokens are found. |
| `parse_summer_excel_memory(excel_path: str) -> Dict[str, Any]` | Ingests summer temperature workbooks across 5 forecast days. Extracts base temperature ranges and calculates district-specific `tmax` and `tmin` using empirical offset tables. |
| `parse_any_excel_memory(excel_path: str) -> Dict[str, Any]` | Router function that dynamically delegates to `parse_summer_excel_memory` or `parse_multi_hazard_excel_memory` based on filename inspection. |
| `parse_rain_excel(...)` / `parse_summer_excel(...)` | Backward-compatibility wrappers maintaining legacy method signatures while routing directly to in-memory routines. |
| `match_district_meta(raw_dist_name: str) -> Tuple[str, str, float, float]` | Resolves a raw district string from an Excel cell into `(std_name, code, lat, lon)`. |
| `_normalize_name(name: str) -> str` | Strips all spaces, hyphens, periods, underscores, and parentheses, returning lowercase alphanumeric keys. |
| `parse_spatial_code(val: Any) -> int` | Maps textual spatial coverage tokens (Dry, ISOL, SCT, FWS, WS) to integer classes (1 to 5). |
| `parse_multi_hazard_tokens(cell_val: Any) -> Tuple[int, int, bool]` | Tokenizes compound multi-hazard strings (e.g., `"TSLG4, HR"`), resolving thunderstorm codes (1–4), rainfall intensity codes (1–4), and the boolean flag `has_inten`. |
| `_extract_base_temp(val: Any, default_mid: float = 42.0) -> float` | Uses regex to parse single numbers or temperature range strings (e.g., `"42-44"`), returning the arithmetic midpoint. |

### 3.2 Canonical District Resolution Architecture
Telangana consists of 33 administrative districts. The normalization system ensures that non-standard spelling or historic abbreviations in raw forecast sheets map directly to the official shapefile boundary name (`Dist_Name`):

```python
# Snippet from utils/excel_parser.py
CANONICAL_DISTRICTS = {
    "adilabad": ("Adilabad", "ADL", 19.65, 78.53),
    "komarambheem": ("Kumurambheem Asifabad", "KMB", 19.32656, 79.20103),
    "kumurambheemasifabad": ("Kumurambheem Asifabad", "KMB", 19.32656, 79.20103),
    "bkothagudem": ("Bhadradri Kothagudem", "BDDK", 17.83, 80.83),
    "bhadradrikothagudem": ("Bhadradri Kothagudem", "BDDK", 17.83, 80.83),
    "hanumakonda": ("Hanumakonda", "WRGU", 18.03792, 79.4698),
    "hanumakondau": ("Hanumakonda", "WRGU", 18.03792, 79.4698),
    "jagtial": ("Jagtial", "JGTL", 18.86, 78.84),
    "jagitial": ("Jagtial", "JGTL", 18.86, 78.84),
    "jangaon": ("Jangoan", "JNG", 17.76317, 79.27668),
    "jayashankarbhupalpally": ("Jayashankar Bhupalpally", "JSKB", 18.50729, 79.91179),
    "peddapalli": ("Peddapalli", "PPL", 18.63, 79.42),
    "peddapalle": ("Peddapalli", "PPL", 18.63, 79.42),
    "rajannasircilla": ("Rajanna Sircilla", "RJNS", 18.42, 78.76),
    "warangal": ("Warangal", "WRGR", 17.9324, 79.78437),
    "warangalr": ("Warangal", "WRGR", 17.9324, 79.78437),
    "yadadribhuvanagiri": ("Yadadri Bhuvanagiri", "YDDB", 17.59, 78.94),
    # ... encompasses all 33 canonical Telangana districts
}
```

---

## 4. PyQGIS Vector Pipeline Implementation (`scripts/imd_automation.py`)

### 4.1 Headless QGIS Execution Cycle
The vector pipeline initializes the standalone QGIS application instance without a desktop display:
```python
from qgis.core import QgsApplication
from qgis.analysis import QgsNativeAlgorithms

QgsApplication.setPrefixPath(config.QGIS_PREFIX, True)
_qgs_app = QgsApplication([], False)
_qgs_app.initQgis()

import processing
from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
```

### 4.2 In-Memory GeoPackage Staging (`join_memory_data_to_shapefile`)
Rather than joining CSV files via QGIS layer joins (which causes locking and performance issues), the pipeline clones the base shapefile geometry into a GeoPackage table in `output/` (`SpatialJoined.gpkg`, `WarningJoined.gpkg`, etc.) and injects attributes programmatically:
```python
def join_memory_data_to_shapefile(district_layer, districts_data, shp_name_field, data_fields, output_gpkg):
    # 1. Clone district_layer into GeoPackage using QgsVectorFileWriter
    # 2. Add dynamic QgsField attributes (Double for temperatures, Int for warning codes)
    # 3. Iterate features, match normalized name, populate feature attributes
    # 4. Commit changes atomically and return output_gpkg path
```

### 4.3 Adaptive Centroid & Collision-Free Labeling
To prevent label truncation or overlapping across small geographic polygons:
* Standard districts use `add_district_labels()` with adaptive SQL expressions:
  ```sql
  CASE 
    WHEN "Dist_Name" = 'Hyderabad' THEN 6.8 
    WHEN "Dist_Name" IN ('Medchal Malkajgiri', 'Hanumakonda', 'Warangal', 'Rajanna Sircilla') THEN 7.5 
    WHEN length("Dist_Name") > 18 THEN 7.8 
    WHEN length("Dist_Name") > 12 THEN 8.4 
    ELSE 9.0 
  END
  ```
* Rainfall intensity labels use `add_rainfall_intensity_district_labels()`, which applies explicit coordinate overrides from `RAINFALL_DISTRICT_CONFIG` (`lx`, `ly`) to guarantee clear visibility when cloud icons are displayed.

### 4.4 Strict Post-Export Quality Check (`quality_check_output_strict`)
Every exported map (PNG and PDF) is inspected immediately after export:
```python
def quality_check_output_strict(path, min_kb=None):
    min_kb = min_kb or MIN_OUTPUT_KB  # Default: 50 KB
    if not os.path.exists(path):
        raise Exception(f"[QC FAIL] Output file missing: {path}")
    size_kb = os.path.getsize(path) / 1024
    if size_kb < min_kb:
        raise Exception(f"[QC FAIL] Output suspiciously small ({size_kb:.1f} KB < {min_kb} KB)")
```

---

## 5. Thunderstorm Warning Module (`scripts/imd_thunderstorm_warning_layout.py`)

Renders the 5-day thunderstorm and wind warning series.

### 5.1 Weather Symbology Placement
* Generates an in-memory point layer (`Point?crs=EPSG:4326`) with attributes `symbol_type` and `sym_size`.
* Positions icons using `DISTRICT_ANCHORS` (`sx`, `sy`) for all 33 districts.
* For districts without explicit anchors, calculates `geom.poleOfInaccessibility(0.002)`.
* Symbol types:
  * `windsock`: For warning values $< 2$ (`windsock.svg` or `Wind_warning.png`).
  * `thunderstorm_wind`: For warning values $\ge 2$ (`cloud.png` or `thunderstorm_wind.svg`).

### 5.2 Multi-Line District Display Names (`DISTRICT_DISPLAY_NAMES`)
Formats district names with strategic newline breaks for cartographic aesthetics:
* `"Bhadradri Kothagudem"` $\rightarrow$ `"Bhadradri\nKothagudem"`
* `"Jayashankar Bhupalpally"` $\rightarrow$ `"Jayashankar\nBhupalpally"`
* `"Jogulamba Gadwal"` $\rightarrow$ `"Jogulamba\nGadwal"`
* `"Kumurambheem Asifabad"` $\rightarrow$ `"Kumurambheem\nAsifabad"`
* `"Medchal Malkajgiri"` $\rightarrow$ `"Medchal\nMalkajgiri"`
* `"Rajanna Sircilla"` $\rightarrow$ `"Rajanna\nSircilla"`
* `"Yadadri Bhuvanagiri"` $\rightarrow$ `"Yadadri\nBhuvanagiri"`

---

## 6. Temperature Grid Summary Layout Engine (`scripts/imd_5day_temp_grid_layout.py`)

Generates the official single-page 3+2 A4 landscape grid summary bulletins:
* `max_temp_5day_summary.png` & `.pdf` (Maximum Temperature Forecast)
* `min_temp_5day_summary.png` & `.pdf` (Minimum Temperature Forecast)

### 6.1 Layout Grid Geometry (A4 Landscape: $297 \times 210$ mm)
* Column Width: $89.0$ mm | Panel Height: $78.0$ mm | Gutter X: $7.0$ mm | Gutter Y: $5.0$ mm
* Row 1 ($Y = 36.5$ mm): Day 1 Forecast (Col 0), Day 2 Forecast (Col 1), Day 3 Forecast (Col 2).
* Row 2 ($Y = 119.5$ mm): Day 4 Forecast (Col 0), Day 5 Forecast (Col 1), **Cell 6 Legend & Directory** (Col 2).

### 6.2 Cell 6 Reference Panel Design
Cell 6 is subdivided into two dedicated components:
1. **Warning Scale Legend** ($Y = 126.3$ mm): 4 color-coded rectangular patches displaying the Heatwave / Coldwave scale with corresponding temperature brackets.
2. **Telangana Districts Directory (33)** ($Y = 146.3$ mm): A structured 3-column reference table mapping all 33 district three-letter codes to their full names, formatted via `DISTRICT_DIRECTORY_3COL`.

---

## 7. Backend Service & REST API Implementation (`serve_dashboard.py`)

### 7.1 Server Architecture
The server is built on Python's standard `ThreadingHTTPServer` and `SimpleHTTPRequestHandler`:
* Configured with `allow_reuse_address = True` and `daemon_threads = True`.
* Automatically attempts port `8765`, scanning up through `8769` if port binding fails.
* Serves the dashboard directly on root `/` and cleanly 302-redirects `/templates/dashboard.html` to root.

### 7.2 REST API Specification

| Endpoint | HTTP Method | Parameters | Response Schema / Action |
| :--- | :---: | :--- | :--- |
| `/api/status` | `GET` | None | Returns JSON object containing `pipeline_running`, `pipeline_status`, `run_status`, `health_status`, `excel_inputs`, and `maps` list. |
| `/api/download_all` | `GET` | `?type=all\|png\|pdf` | Generates on-the-fly streaming ZIP archive of generated maps with `Content-Disposition: attachment`. |
| `/api/download_all_png` | `GET` | None | Convenience endpoint streaming all high-res PNG maps in a ZIP archive. |
| `/api/download_all_pdf` | `GET` | None | Convenience endpoint streaming all official PDF bulletins in a ZIP archive. |
| `/api/upload` | `POST` | Multipart Form | Extracts uploaded `.xlsx` files and saves them to `data/input/`. Returns `{success: true, files: [...]}`. |
| `/api/delete_workbook` | `POST` | `?file=<filename>` | Deletes the specified workbook from `data/input/`. |
| `/api/parse_excel` | `POST` | None | Validates in-memory parsing capability across all workbooks in `data/input/` without running the map generation pipeline. |
| `/api/run_pipeline` | `POST` | `?module=all\|rain\|summer` | Spawns a background thread running `imd_automation.py` with the selected module parameter. |
| `/api/run_rain_pipeline` | `POST` | None | Triggers rain and warning map generation in background thread. |
| `/api/run_summer_pipeline` | `POST` | None | Triggers summer temperature map generation in background thread. |

---

## 8. Supporting Production Utilities

### 8.1 Atomic JSON Operations (`utils/atomic_json.py`)
Prevents telemetry corruption during concurrent read/write operations:
* `atomic_write_json(path, data, indent=2)`: Writes to `path + ".tmp"`, flushes buffer, executes `os.fsync(f.fileno())`, and executes `os.replace(tmp, path)`.
* `read_json_safe(path, default=None)`: Safely reads JSON; on decode error, attempts reading from `.tmp` fallback before returning default.

### 8.2 Standardized Logging (`utils/imd_logger.py`)
* Provides `TimedRotatingFileHandler` configured for midnight rotation with 14-day retention.
* Includes ANSI color formatting (`_ColourFormatter`) with Windows console support via `kernel32.SetConsoleMode`.
* Provides `make_legacy_log_fn` to bridge legacy scripts to the standardized logger.

### 8.3 Central Configuration (`config.py`)
* Automatically detects QGIS root across Windows (`C:\Program Files\QGIS*`, `C:\OSGeo4W*`) and Linux (`/usr`).
* Auto-detects QGIS Python runner (`python-qgis-ltr.bat`, `python-qgis.bat`, `python.exe`).
* Validates directory structures and SVG assets during startup via `_check()`.

---

## 9. Developer CLI Commands & Testing

### 9.1 Executing the Vector Pipeline via Command Line
```powershell
# Auto-detect QGIS and run the full pipeline
.\run_imd_automation.bat

# Direct execution using QGIS standalone Python:
& "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" scripts\imd_automation.py --module=all

# Execute only rainfall modules:
& "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" scripts\imd_automation.py --module=rain

# Execute only summer temperature modules:
& "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" scripts\imd_automation.py --module=summer

# Test individual layout modules directly:
& "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" scripts\imd_5day_temp_grid_layout.py
& "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" scripts\imd_thunderstorm_warning_layout.py
```

### 9.2 Starting the Operational Dashboard
```powershell
# Using the Windows batch launcher:
.\open_dashboard.bat

# Or starting directly via Python:
python serve_dashboard.py 8765
```

---

## 10. Engineering Best Practices & Contribution Guidelines

1. **Strict Zero-CSV Policy**: Do not introduce temporary disk CSV files. All tabular transformations must occur in memory via `openpyxl` and be bound to GeoPackages or memory layers.
2. **Preserve Documentation Integrity**: Do not embed passwords, server IPs, internal URLs, or personal machine paths in source code or documentation.
3. **Deterministic Cleanups**: Always wrap layout creation and layer registration in `try...finally` blocks, ensuring `project.clear()`, layer dereferencing, and `gc.collect()` run after every export pass.
4. **Validation First**: Always verify that `quality_check_output_strict` succeeds for all output formats before marking a pipeline task complete.
