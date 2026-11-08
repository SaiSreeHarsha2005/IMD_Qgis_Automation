# PROJECT REPORT: Automated Spatial Data Processing and Thematic Map Generation in QGIS using Python
**Meteorological Centre Hyderabad — India Meteorological Department (IMD)**  
*Ministry of Earth Sciences (MoES), Government of India*

---

## 1. Project Identification & Executive Summary

* **Project Title:** Automated Spatial Data Processing and Thematic Map Generation in QGIS using Python
* **Government Agency:** India Meteorological Department (IMD), Ministry of Earth Sciences (MoES), Government of India
* **Operational Centre:** Meteorological Centre Hyderabad, Telangana, India
* **System Version:** 2.0 (Direct In-Memory Excel Ingestion & PyQGIS Automation Engine)
* **Project Team:**
  * **Minnekanti Sai Sree Harsha** (Project Lead & System Developer)
  * **S Nyneeta Rao** (Co-Developer & Cartographic Layout Design)
  * *Academic Institution:* Department of Computer Science & Engineering, Geethanjali College of Engineering and Technology, Hyderabad
* **Submission & Delivery Date:** June 2026

### Executive Summary
The India Meteorological Department (IMD), under the Ministry of Earth Sciences (MoES), is responsible for meteorological observations, weather forecasting, and severe weather warnings across India. At the regional level, Meteorological Centre Hyderabad issues daily forecast bulletins, agricultural advisories, and disaster alerts across the 33 administrative districts of Telangana.

Historically, transforming raw forecast tables into geospatial thematic maps was a labor-intensive, manual process taking 45 to 60 minutes each shift. Previous automation scripts attempted to convert spreadsheets into intermediate CSV files on disk, which repeatedly caused file-locking conflicts, encoding errors, and data corruption.

This project delivers a production-grade, end-to-end geospatial automation platform. Featuring a **Direct In-Memory Excel Ingestion Engine (Zero-CSV)**, an automated **PyQGIS Cartographic Renderer**, and a **Multi-Threaded Operational Telemetry Dashboard**, the system ingests daily forecast spreadsheets, validates and normalizes district names against official boundary polygons, binds attributes into in-memory GeoPackage vector structures, and renders up to **58 publication-grade thematic maps** (300 DPI PNG and vector PDF) in **under two minutes** ($\approx 111$ seconds).

---

## 2. Problem Statement & Operational Objectives

### 2.1 The Operational Problem
Daily operations at regional meteorological centres follow strict deadlines for media broadcasts, state disaster management briefings, and web portal publication. The manual and semi-automated GIS workflows previously in place suffered from four critical operational challenges:

1. **Manual Data Entry Overhead:**
   Every morning and evening, GIS operators manually keyed district rainfall probabilities, hazard alert levels, and temperature forecasts into desktop GIS software. This tedious process took 45 to 60 minutes daily and was highly susceptible to human clerical error.
2. **Intermediate CSV Failure Modes:**
   Early automation attempts relied on intermediate CSV conversion scripts. These suffered from:
   * **Windows File-Locking (`WinError 32`):** Simultaneous access by background workers and web servers caused permission crashes.
   * **Encoding Mismatches:** Differences between UTF-8 and ANSI/CP1252 corrupted special characters and district names.
   * **Data Truncation:** Multi-line forecast cells or multi-hazard tokens were improperly parsed or split across rows.
3. **Cartographic Inconsistency:**
   Manual adjustment of print layouts frequently produced misaligned legends, shifted scale bars, inconsistent typography, and overlapping labels—especially for districts with lengthy administrative names.
4. **Lack of Operational Visibility:**
   Operators lacked a unified interface to inspect workbook readiness, trigger on-demand generation, monitor live progress, and batch-download generated bulletins.

### 2.2 Project Objectives
* **Zero-CSV Direct Ingestion:** Eliminate all temporary disk CSV files by parsing Excel workbooks directly into Python memory buffers via `openpyxl`.
* **Canonical 33-District Normalization:** Implement an automated dictionary and regex normalization engine that maps any administrative or spelling variation directly to the canonical Telangana shapefile boundary.
* **Complete Cartographic Automation:** Automatically generate the full suite of operational weather maps: 7-Day Spatial Rainfall Forecast, 5-Day Thunderstorm Warnings, 5-Day Rainfall Intensity Warnings, 5-Day Maximum/Minimum Temperature Forecasts, and 5-Day Temperature Grid Summary Bulletins.
* **High-Resolution Dual-Format Output:** Render all maps at publication standards (300 DPI high-resolution PNG for digital media and vector PDF for official print bulletins).
* **Operational Telemetry Dashboard:** Provide an institutional web interface with real-time status tracking, drag-and-drop file ingestion, live progress indicators, and instant streaming ZIP downloads.

---

## 3. System Architecture & Methodology

The platform implements a modular four-tier architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM ARCHITECTURE MODEL                       │
├────────────────────────────────────────────────────────────────────────┤
│  1. INGESTION TIER       Direct Excel Ingestion (utils/excel_parser.py)│
│                          • In-memory openpyxl parser (Zero-CSV)        │
│                          • Multi-Hazard compound token parser          │
│                          • 33-district canonical synonym matcher       │
├────────────────────────────────────────────────────────────────────────┤
│  2. VECTOR & STAGING     In-Memory GeoPackage Staging                  │
│     TIER                 • Base layer: data/shapefiles/District_Bound..│
│                          • Staged GPKG tables (*Joined.gpkg)           │
│                          • Atomic vector attribute population          │
├────────────────────────────────────────────────────────────────────────┤
│  3. CARTOGRAPHIC TIER    Headless PyQGIS Rendering Engine              │
│                          • scripts/imd_automation.py (Main engine)     │
│                          • scripts/imd_thunderstorm_warning_layout.py  │
│                          • scripts/imd_5day_temp_grid_layout.py        │
│                          • Graduated fill, anchored SVGs, halo labels  │
├────────────────────────────────────────────────────────────────────────┤
│  4. REST & TELEMETRY     serve_dashboard.py (Port 8765)                │
│     TIER                 • Python standard library ThreadingHTTPServer │
│                          • templates/dashboard.html live interface     │
│                          • Real-time polling & dynamic ZIP streaming   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technical Specifications & Output Products

The platform automatically produces up to **58 high-resolution cartographic files** across five major operational categories:

| Map Product Category | Forecasting Horizon | Generated File Outputs | Formats & DPI | Cartographic Styling & Symbology |
| :--- | :---: | :--- | :--- | :--- |
| **7-Day Spatial Rainfall Forecast** | Days 1 to 7 | `rainfall_forecast_day1` to `day7` (14 files) | 300 DPI PNG + Vector PDF | 5-tier spatial coverage: Dry (`#FFFFFF`), Isolated (`#6BEA48`), Scattered (`#0A7A32`), Fairly Widespread (`#56ACE6`), Widespread (`#2E73D8`). Adaptive text labeling. |
| **5-Day Thunderstorm & Wind Warning** | Days 1 to 5 | `thunderstorm_warning_day1` to `day5` (10 files) | 300 DPI PNG + Vector PDF | 4-tier alert scale: Nil (`#009900`), Watch (`#FFFF00`), Alert (`#FF9900`), Warning (`#FF0000`). Anchored SVG wind socks and lightning clouds. Dual advisory cards. |
| **5-Day Rainfall Intensity Warning** | Days 1 to 5 | `rainfall_intensity_day1` to `day5` (10 files) | 300 DPI PNG + Vector PDF | Multi-hazard rainfall intensity: Nil, Heavy Rain, Very Heavy Rain, Extremely Heavy Rain with cloud SVG indicators. (Generated conditionally when heavy rain is present). |
| **5-Day Maximum Temperature Forecast** | Days 1 to 5 | `tmax_day1_<DATE>` to `day5_<DATE>` (10 files) | 300 DPI PNG + Vector PDF | Heatwave scale: Normal $\le 40^\circ\text{C}$ (`#2E7D32`), Be Alert $41–45^\circ\text{C}$ (`#FFD54F`), Be Prepared $46–47^\circ\text{C}$ (`#FB8C00`), Warning $>47^\circ\text{C}$ (`#D32F2F`). |
| **5-Day Minimum Temperature Forecast** | Days 1 to 5 | `tmin_day1_<DATE>` to `day5_<DATE>` (10 files) | 300 DPI PNG + Vector PDF | Coldwave scale: Warning $<5^\circ\text{C}$ (`#D32F2F`), Alert $5–10^\circ\text{C}$ (`#FB8C00`), Watch $11–15^\circ\text{C}$ (`#FFD54F`), Normal $>15^\circ\text{C}$ (`#2E7D32`). |
| **5-Day Temperature Grid Summary Bulletins** | 5-Day Consolidated | `max_temp_5day_summary`<br>`min_temp_5day_summary` (4 files) | 300 DPI PNG + Vector PDF | Official 3+2 A4 landscape grid summary layout combining Days 1–5 forecast viewports with warning scale and 33-district abbreviation directory. |

---

## 5. Key Engineering Innovations

1. **Direct In-Memory Excel Ingestion (`utils/excel_parser.py`):**
   * Eliminates disk CSV bottlenecks entirely.
   * Uses `openpyxl` with `data_only=True` to extract raw values.
   * Auto-detects shifting header rows within the first 5 rows of input sheets.
   * Parses compound multi-hazard strings (`"TSLG4, HR"`) into distinct warning levels and intensity codes.
2. **Canonical 33-District Normalization:**
   * Uses regex-based alphanumeric stripping combined with an authoritative lookup table (`CANONICAL_DISTRICTS`) and centroid coordinates.
   * Automatically resolves administrative spelling variations (*Komaram Bheem* vs. *Kumurambheem Asifabad*, *Bkothagudem* vs. *Bhadradri Kothagudem*, *Jangaon* vs. *Jangoan*).
3. **GeoPackage Attribute Binding (`join_memory_data_to_shapefile`):**
   * Avoids fragile GUI-style QGIS layer joins.
   * Clones base vector geometry into temporary GeoPackage tables, binds dynamically created attributes, and executes atomic transactions.
4. **Collision-Free Dynamic Labeling:**
   * Implements SQL expression-driven adaptive font sizing ($6.8\text{ pt}$ for *Hyderabad*, $7.5\text{ pt}$ for *Medchal Malkajgiri*, up to $9.0\text{ pt}$ for standard districts).
   * Enforces white halo buffers ($0.85 - 1.20\text{ mm}$) to guarantee high-contrast readability against saturated map fills.
5. **Anchored Weather Symbology with Inaccessibility Fallback:**
   * Utilizes curated district anchor coordinates (`DISTRICT_ANCHORS`) to position convective cloud and wind symbols.
   * Implements automated fallback using `geom.poleOfInaccessibility(0.002)` to guarantee that icons remain strictly within polygon borders.
6. **Thread-Safe Telemetry & Zero-Dependency REST Server (`serve_dashboard.py`):**
   * Built on Python's built-in `ThreadingHTTPServer` to run in restricted or air-gapped government environments without external framework dependencies.
   * Thread synchronization via `threading.Lock()` prevents concurrent execution collisions.
   * Atomic file writing (`utils.atomic_json.atomic_write_json`) guarantees corruption-proof telemetry polling.

---

## 6. Performance Benchmarks & Validation Results

The completed system was benchmarked in operational test runs on standard workstation hardware:

| Benchmark Metric | Manual GIS Workflow | Legacy CSV Scripts | Delivered 2.0 System | Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Total Production Time (All Maps)** | 45–60 minutes | 6–8 minutes (with failures) | **111 seconds** ($\approx 1.85$ min) | **>95% Time Reduction** |
| **Intermediate Disk CSV Files** | 0 files | 7 to 12 CSV files | **0 files (Pure In-Memory)** | **100% Elimination** |
| **District Match Accuracy** | Dependent on operator | ~85% (spelling failures) | **100% (33 of 33 Districts)** | **Zero Mismatches** |
| **Quality Control Pass Rate** | Manual inspection | Occasional empty maps | **100% (>50 KB Strict QC Check)** | **Fully Deterministic** |
| **Output Products Generated** | 5 to 10 maps (partial) | 24 maps | **Up to 58 Maps (PNG + PDF)** | **Comprehensive Coverage** |

---

## 7. Conclusion & Operational Impact

The **Automated Spatial Data Processing and Thematic Map Generation** system successfully modernizes daily operational cartography at the India Meteorological Department (IMD), Meteorological Centre Hyderabad.

### Operational Benefits Realized:
1. **Dramatic Acceleration of Warning Dissemination:** Bulletin generation time has been reduced from one hour to under two minutes, enabling earlier dissemination of severe weather warnings to state disaster management authorities.
2. **Complete Data Integrity:** In-memory Excel ingestion eliminates CSV-related data corruption, character truncation, and file-locking errors.
3. **Cartographic Standardization:** Every issued bulletin strictly complies with official IMD branding guidelines, official color ramps, and high-resolution publication standards.
4. **Intuitive Operational Workflow:** Forecasters can manage workbooks, trigger generation, inspect live progress, and batch-download bulletins through a responsive web interface or automated batch scripts.
