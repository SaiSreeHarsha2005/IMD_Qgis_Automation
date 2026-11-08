# USER MANUAL: Automated Spatial Data Processing and Thematic Map Generation in QGIS using Python
**Meteorological Centre Hyderabad — India Meteorological Department (IMD)**  
*Ministry of Earth Sciences (MoES), Government of India*

---

## 1. Document Control & Institutional Information

* **Document Title:** Operational User Manual — Automated Meteorological Thematic Map Generation Platform
* **Operational Centre:** Meteorological Centre Hyderabad, India Meteorological Department (IMD)
* **Target Audience:** Duty Forecasters, Meteorologists, GIS Technical Officers, and Disaster Management Liaisons
* **System Version:** 2.0 (Zero-CSV Direct Excel Ingestion Architecture)
* **Project Team:**
  * **Minnekanti Sai Sree Harsha** (Project Lead & System Developer)
  * **S Nyneeta Rao** (Co-Developer & Cartographic Layout Design)
  * *Academic Institution:* Department of Computer Science & Engineering, Geethanjali College of Engineering and Technology, Hyderabad

---

## 2. System Overview & Operational Capabilities

The **Automated Spatial Data Processing and Thematic Map Generation** system provides an automated mapping pipeline designed to produce official IMD weather forecast bulletins for the 33 districts of Telangana.

Forecasters simply upload raw daily forecast workbooks (`.xlsx`), select the desired generation scope, and the platform automatically renders publication-ready, 300 DPI high-resolution thematic maps in both PNG and vector PDF formats.

### Core Capabilities:
* **Zero-CSV Direct Ingestion:** Operates directly on native Excel workbooks without requiring intermediate CSV conversions, ensuring zero character encoding corruption or file-locking conflicts.
* **58 Thematic Map Products Generated on Demand:**
  1. **7-Day Spatial Rainfall Forecast** (Days 1 to 7)
  2. **5-Day Thunderstorm & Wind Warning** (Days 1 to 5)
  3. **5-Day Rainfall Intensity Warning** (Days 1 to 5, generated conditionally when heavy rainfall is forecasted)
  4. **5-Day Maximum & Minimum Temperature Forecasts** (Days 1 to 5)
  5. **5-Day Temperature Grid Summary Bulletins** (Consolidated 3+2 A4 landscape official bulletins)
* **Real-Time Operational Telemetry:** Built-in web dashboard displaying live progress percentages, current rendering steps, elapsed execution timers, and interactive map galleries.

---

## 3. Operational Workflow Summary

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │  STEP 1: LAUNCH THE OPERATIONAL DASHBOARD                              │
  │  Double-click 'open_dashboard.bat' or open http://localhost:8765/      │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  STEP 2: INGEST FORECAST WORKBOOKS (.xlsx)                             │
  │  Drag & drop Multi_Hazard_*.xlsx or SUMMER.xlsx into the upload zone   │
  │  (Files are saved instantly to data/input/ and verified in memory)     │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  STEP 3: TRIGGER ON-DEMAND MAP GENERATION                              │
  │  Click "Generate Rain & Warning Maps", "Generate Temperature Maps",    │
  │  or "Run All Maps Pipeline"                                            │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  STEP 4: MONITOR REAL-TIME PIPELINE PROGRESS                           │
  │  Watch the live progress bar advance from 0% to 100% with step logs    │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  STEP 5: PREVIEW & DOWNLOAD HIGH-RESOLUTION MAPS                       │
  │  Inspect maps in the interactive gallery or click "Download All PNGs"  │
  │  or "Download All PDFs" for instant ZIP archive packaging              │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Step-by-Step Operating Instructions

### Step 1: Launching the Dashboard

1. Locate the file **`open_dashboard.bat`** in the project root directory.
2. Double-click the file to launch the server.
3. A command prompt window will initialize the background server, release any prior port locks on port `8765`, and automatically open your default browser to:
   ```
   http://localhost:8765/
   ```
4. The dashboard header confirms operational mode (`PROD`), live Indian Standard Time (IST), and server connectivity.

> [!TIP]
> Keep the command prompt window minimized during your operational shift. To stop the server, press `Ctrl + C` in the console window.

---

### Step 2: Preparing and Ingesting Forecast Workbooks

The system ingests two primary Excel workbook types:

#### 1. Multi-Hazard 7-Day Forecast Workbook
* **Naming Convention:** `Multi_Hazard_7_Day_District_Wise_Forecast_Telangana <DATE>.xlsx` (or containing `multi_hazard` / `rain`).
* **Required Sheet:** A sheet named `"7-Day Forecast"` (or the active primary worksheet).
* **Content:**
  * District column listing all 33 Telangana districts.
  * Spatial coverage columns: `Day 1 Forecast` through `Day 7 Forecast` (e.g., *DRY*, *ISOL*, *SCT*, *FWS*, *WS*).
  * Warning columns: `Day 1 Warning` through `Day 5 Warning` (e.g., *TSLG3*, *TSLG4*, *TSLG5*, *HR*, *VHR*, *EHR*).

#### 2. Summer Temperature Forecast Workbook
* **Naming Convention:** `SUMMER.xlsx` (or containing `summer`).
* **Content:** 5-Day maximum and minimum temperature projections per district.

#### Ingestion Procedure:
* **Drag-and-Drop:** Drag your `.xlsx` file directly over the upload zone on the dashboard.
* **Manual Copy:** Alternatively, copy the workbook directly into the `data/input/` folder on your machine.
* The **Direct Excel Input Workbooks** table will immediately update to reflect the workbook name, file size, last modified timestamp, and operational readiness.

---

### Step 3: Triggering Map Generation

The dashboard provides dedicated execution action cards:

| Action Card | Button Label | Operation Executed | Expected Output |
| :--- | :--- | :--- | :--- |
| **Rain & Warning Pipeline** | 🌧️ **Generate Rain & Warning Maps** | Ingests Multi-Hazard workbook. Generates 7-Day Spatial Rainfall, 5-Day Thunderstorm & Wind Warning, and 5-Day Rainfall Intensity maps. | 24 to 34 files (PNG + PDF) |
| **Summer Temperature Pipeline** | ☀️ **Generate Temperature Maps** | Ingests Summer workbook. Generates 10 daily Max/Min temperature maps and 2 official 5-Day Grid Summary Bulletins. | 24 files (PNG + PDF) |
| **Full GIS Automation** | 🚀 **Run All Maps Pipeline** | Full end-to-end execution across all forecast domains in sequence. | Up to 58 files (PNG + PDF) |
| **Excel Ingestion Validator** | 📄 **Validate Excel Ingestion** | Rapid in-memory parsing verification across all 33 districts without rendering layouts. | Instant verification message |

---

### Step 4: Monitoring Live Execution Progress

Once an action button is clicked:
1. The **Executing Map Generation Pipeline** banner appears with an animated progress bar.
2. The indicator reports live execution stages:
   * `10%`: Environment initialization and workbook validation.
   * `50%`: Binding in-memory attributes to the GeoPackage vector layer.
   * `65%`: Rendering 7-Day Spatial Rainfall maps.
   * `75%`: Rendering 5-Day Thunderstorm & Wind Warning maps with anchored SVG symbology.
   * `85%`: Rendering 5-Day Rainfall Intensity maps (if heavy rain tokens are present).
   * `95%`: Rendering Maximum & Minimum Temperature maps and 5-Day Grid Bulletins.
   * `98%`: Strict Quality Control (QC) validation verifying file sizes $> 50\text{ KB}$ and 300 DPI fidelity.
   * `100%`: Completed successfully.

---

### Step 5: Viewing and Downloading Maps

The **Live Generated Map Outputs** gallery updates automatically upon run completion:

1. **Category Filtering:** Filter maps by clicking category pills:
   * **All**
   * 🌧️ **7-Day Spatial**
   * ⚡ **Thunderstorm**
   * ⚠️ **Intensity**
   * 🌡️ **Temperature**
   * 📊 **Bulletins** (5-Day Grid Summaries)
2. **View Modes:**
   * **Table View:** Detailed table displaying file name, category, format, timestamp, and individual download links.
   * **Gallery View:** High-resolution thumbnail grid with click-to-enlarge modal lightbox.
3. **One-Click Batch Downloads:**
   * **Download All PNGs:** Packages all 300 DPI PNG maps into a single ZIP archive.
   * **Download All PDFs:** Packages all vector PDF bulletins into a single ZIP archive.
   * **Download All (ZIP):** Downloads the complete 58-file publication bundle.

---

## 5. Official IMD Legend Scales Reference

### 5.1 7-Day Spatial Rainfall Distribution Scale

| Classification | Abbreviation | Spatial Area Coverage | Official Hex Fill | Cartographic Label |
| :--- | :---: | :---: | :---: | :--- |
| **Dry** | DRY | 0% | `#FFFFFF` | Dry |
| **Isolated** | ISOL | 1% to 25% | `#6BEA48` | One or two places |
| **Scattered** | SCT | 26% to 50% | `#0A7A32` | Few places |
| **Fairly Widespread** | FWS | 51% to 75% | `#56ACE6` | Many places |
| **Widespread** | WS | 76% to 100% | `#2E73D8` | Most places |

---

### 5.2 5-Day Thunderstorm & Wind Warning Alert Levels

| Warning Stage | Threshold / Phenomenon | Official Hex Fill | Applied Symbol | Action Guidance |
| :--- | :--- | :---: | :--- | :--- |
| **No Warning** | No severe convective weather forecasted | `#009900` | None | No action required |
| **Watch** | Sustained surface wind 30–40 kmph / TSLG3 | `#FFFF00` | Windsock icon | Be updated |
| **Alert** | Thunderstorm with wind 40–50 kmph / TSLG4 | `#FF9900` | Lightning cloud icon | Be prepared |
| **Warning** | Squall / severe storm 50–60 kmph / TSLG5 | `#FF0000` | Severe storm icon | Take action |

---

### 5.3 5-Day Rainfall Intensity Warning Scale

| Warning Level | Rainfall Category | 24-Hour Precipitation | Applied Hex Fill | Cloud Symbol Indicator |
| :--- | :--- | :---: | :---: | :--- |
| **No Warning** | Light to moderate rain | $< 64.5$ mm | `#009900` | `cloud_light_rain.svg` |
| **Watch** | Heavy rain (HR) | $64.5 - 115.5$ mm | `#FFFF00` | `cloud_moderate_rain.svg` |
| **Alert** | Very heavy rain (VHR) | $115.6 - 204.4$ mm | `#FF9900` | `cloud_heavy_rain.svg` |
| **Warning** | Extremely heavy rain (EHR) | $> 204.4$ mm | `#FF0000` | `cloud_extreme_rain.svg` |

---

### 5.4 Maximum Temperature Forecast (Heatwave Scale)

| Alert Status | Temperature Range ($^\circ\text{C}$) | Official Hex Fill | Public Advisory |
| :--- | :---: | :---: | :--- |
| **No Warning** | $\le 40.0^\circ\text{C}$ | `#2E7D32` | Normal summer conditions |
| **Be Alert** | $41.0^\circ\text{C} - 45.0^\circ\text{C}$ | `#FFD54F` | Moderate heat stress; stay hydrated |
| **Be Prepared** | $46.0^\circ\text{C} - 47.0^\circ\text{C}$ | `#FB8C00` | Severe heat; avoid peak afternoon sun |
| **Warning** | $> 47.0^\circ\text{C}$ | `#D32F2F` | Extreme heat emergency; take urgent action |

---

## 6. Headless Command-Line Execution for Technical Operators

For automated workflows, scheduled scripts, or remote server sessions:

```powershell
# Run the complete suite using the batch runner:
.\run_imd_automation.bat

# Direct execution via QGIS standalone Python:
& "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" scripts\imd_automation.py --module=all
```

Execution outputs will be logged to `logs/automation_log.txt` and generated maps placed in `output/`.

---

## 7. Operator Troubleshooting & Frequently Asked Questions

#### Q1: Where are the generated maps saved on my computer?
* **Answer:** All 300 DPI PNG and vector PDF maps are automatically saved to the **`output/`** folder located directly in the project root directory.

#### Q2: What should I do if the dashboard displays "A pipeline is already running"?
* **Answer:** The system enforces single-instance thread safety to prevent layout collisions. Allow the ongoing run to finish (typically 60–110 seconds) or inspect `logs/run_status.json`.

#### Q3: What happens if heavy rainfall is not forecasted for the week?
* **Answer:** The engine inspects warning tokens across all districts. If no heavy rainfall tokens (`HR`, `VHR`, `EHR`) are present, the system automatically skips rainfall intensity maps and logs:
  `[INFO] No heavy rainfall intensity tokens present — intensity maps skipped.`
  In this scenario, 48 maps are generated instead of 58 maps.

#### Q4: How do I know if an uploaded workbook was recognized?
* **Answer:** Check the **Direct Excel Input Workbooks** table. If the workbook has a green `READY` badge and displays the correct file size and timestamp, it is valid and ready for execution.
