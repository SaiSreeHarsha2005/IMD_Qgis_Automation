# DEPLOYMENT GUIDE: Automated Spatial Data Processing and Thematic Map Generation in QGIS using Python
**Meteorological Centre Hyderabad — India Meteorological Department (IMD)**  
*Ministry of Earth Sciences (MoES), Government of India*

---

## 1. System Requirements & Prerequisites

The platform is designed to operate on production workstations or dedicated servers in both Windows and Linux environments.

### 1.1 Hardware Specifications
* **CPU:** Quad-Core x86_64 processor (Intel Core i5/i7/Xeon or AMD Ryzen 5/7 equivalent) or higher.
* **RAM:** 8 GB minimum (16 GB recommended for concurrent batch rendering).
* **Disk Space:** 5 GB free disk space (accounting for QGIS runtime, base shapefiles, and rolling map archives).
* **Display / Cartography:** A4 landscape resolution capability ($297 \times 210$ mm rendering target at 300 DPI).

### 1.2 Software Prerequisites

#### Windows Environments (Workstation / Windows Server)
* **Operating System:** Windows 10 / 11 / Windows Server 2019/2022 (64-bit).
* **GIS Engine:** QGIS Long Term Release (LTR) 3.x (e.g., QGIS 3.44.14, QGIS 3.34 LTR, or OSGeo4W standalone).
* **Python Runtime:** Python 3.12+ (pre-packaged within the QGIS installation directory).
* **Python Libraries:** `openpyxl` (included by default in QGIS LTR Python site-packages).

#### Linux Environments (Ubuntu / Debian Server)
* **Operating System:** Ubuntu 22.04 LTS / 24.04 LTS or Debian 12 (64-bit).
* **Packages:** `qgis`, `python3-qgis`, `xvfb`, `fonts-dejavu`, `fonts-liberation`, `python3-openpyxl`, `python3-pip`.
* **Headless Display:** `QT_QPA_PLATFORM=offscreen` (or virtual framebuffer via Xvfb).

---

## 2. Directory Setup & Asset Verification

1. **Clone or Extract Project Files:**
   Place the project files into a dedicated operational path (e.g., `C:\IMD_AUTOMATION\` on Windows or `/opt/imd_automation/` on Linux).

2. **Verify Required Base Assets:**
   Prior to initial execution, ensure the following core directories and files are present:
   * **Boundary Shapefiles (`data/shapefiles/`):**
     * `District_Boundary.shp` (33 Telangana revenue districts)
     * `District_Boundary.dbf`, `District_Boundary.prj`, `District_Boundary.shx`
   * **Cartographic Symbols (`templates/symbols/`):**
     * `NorthArrow_04.svg`
     * `cloud_light_rain.svg`, `cloud_moderate_rain.svg`, `cloud_heavy_rain.svg`, `cloud_extreme_rain.svg`
     * `windsock.svg`, `thunderstorm_wind.svg`, `thunderstorm.svg`, `Wind_warning.png`, `cloud.png`
   * **Official Logos (`templates/`):**
     * `IMD_LOGO.png`

3. **Verify Configuration (`config.py`):**
   The central configuration auto-detects QGIS. Run the configuration check:
   ```powershell
   python config.py
   ```
   A successful verification will report:
   ```
   [CONFIG OK]  PROJECT_ROOT=<path>  MODE=PROD  QGIS=<qgis_path>  PYTHON=<python_bin>
   ```

---

## 3. Windows Production Deployment

### 3.1 Option A: Interactive Web Dashboard (Recommended)

1. **Launch the Server:**
   Execute `open_dashboard.bat` from File Explorer or Command Prompt:
   ```cmd
   open_dashboard.bat
   ```
   The batch script will:
   * Scan system directories for QGIS Python (`python-qgis-ltr.bat`, `python-qgis.bat`, `python.exe`).
   * Terminate any lingering process bound to port `8765`.
   * Start `serve_dashboard.py 8765` in background mode.
   * Launch your default browser to `http://localhost:8765/`.

2. **Operational Access:**
   * Forecasters access the dashboard at `http://localhost:8765/` (or via the machine's local intranet IP).
   * Files uploaded through the UI are immediately written to `data/input/` and available for execution.

---

### 3.2 Option B: Headless Command-Line Execution

To run map generation without launching a web browser:

```powershell
# Automated batch execution (auto-detects QGIS):
.\run_imd_automation.bat

# Direct execution with specific module targeting:
& "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" scripts\imd_automation.py --module=all
```

Supported CLI flags:
* `--module=all`: Generates 7-Day Spatial, 5-Day Thunderstorm, 5-Day Rainfall Intensity, 5-Day Temperature, and Grid Bulletins (up to 58 maps).
* `--module=rain`: Generates Spatial, Thunderstorm, and Rainfall Intensity maps.
* `--module=summer`: Generates daily Max/Min temperature maps and 5-Day Grid Summary Bulletins.
* `--input="<path_to_xlsx>"`: Explicitly specifies the input forecast workbook.

---

### 3.3 Automated Scheduling via Windows Task Scheduler

To execute map generation automatically on arrival of daily forecast workbooks (e.g., at 08:30 IST and 17:30 IST):

1. Open **Task Scheduler** (`taskschd.msc`).
2. Click **Create Basic Task** $\rightarrow$ Name: `IMD_Daily_Map_Automation`.
3. Set Trigger to **Daily** at `08:30:00` (and repeat for evening at `17:30:00`).
4. Action $\rightarrow$ **Start a program**:
   * **Program/script:** `cmd.exe`
   * **Add arguments:** `/c run_imd_automation.bat`
   * **Start in:** `C:\path\to\IMD_AUTOMATION_FINALL\`
5. Check **Run whether user is logged on or not** and select **Run with highest privileges**.

---

## 4. Linux / Ubuntu Server Headless Deployment

For dedicated rack servers or virtual machines running Ubuntu 22.04 / 24.04 LTS:

### 4.1 Deployment Script (`deploy_linux.sh`)

1. Make the script executable and run with administrative privileges:
   ```bash
   chmod +x deploy_linux.sh
   sudo ./deploy_linux.sh
   ```

2. **What `deploy_linux.sh` executes:**
   * Installs system packages: `qgis`, `python3-qgis`, `xvfb`, `fonts-dejavu`, `fonts-liberation`, `python3-openpyxl`, `python3-pip`.
   * Sets folder permissions (`chmod -R 775`).
   * Configures offscreen rendering (`QT_QPA_PLATFORM=offscreen`).
   * Registers and enables a systemd service: `imd-dashboard.service`.

### 4.2 Systemd Service Unit (`/etc/systemd/system/imd-dashboard.service`)

```ini
[Unit]
Description=IMD Hyderabad Automated Map Generation Dashboard
After=network.target

[Service]
Type=simple
User=imduser
WorkingDirectory=/opt/imd_automation
Environment="QT_QPA_PLATFORM=offscreen"
Environment="PYTHONPATH=/opt/imd_automation:/opt/imd_automation/scripts:/opt/imd_automation/utils"
ExecStart=/usr/bin/python3 /opt/imd_automation/serve_dashboard.py 8765
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4.3 Managing the Linux Service

```bash
# Check service status
sudo systemctl status imd-dashboard

# Restart service
sudo systemctl restart imd-dashboard

# View real-time service logs
journalctl -u imd-dashboard -f
```

> [!NOTE]
> For network security in public and institutional GitHub deployments, always bind internal IP addresses or hostnames through reverse proxies (e.g., Nginx) and avoid hardcoding internal server IPs in production deployment scripts.

---

## 5. Post-Deployment Verification & Smoke Testing

Execute the following verification sequence to confirm end-to-end operational readiness:

### 1. HTTP Endpoint Check
Test backend telemetry using `curl` or a web browser:
```bash
curl -s http://localhost:8765/api/status | grep "timestamp"
```
*Expected Output:* A JSON object with valid timestamp, system health, and input workbook details.

### 2. In-Memory Excel Ingestion Validation
Verify that uploaded forecast sheets parse cleanly without errors:
```bash
curl -s -X POST http://localhost:8765/api/parse_excel
```
*Expected Output:* `{"success": true, "message": "Direct Excel Engine: Verified in-memory parsing..."}`.

### 3. Pipeline Test Execution
Trigger a test run across the rainfall module:
```bash
curl -s -X POST http://localhost:8765/api/run_rain_pipeline
```
Monitor `logs/run_status.json` until `"progress": 100` and `"status": "SUCCESS"`.

### 4. Cartographic Quality Validation
Inspect the `output/` directory:
```powershell
Get-ChildItem output\ -Filter *.png | Measure-Object
```
* Confirm that generated PNG files are approximately $800\text{ KB} - 1.5\text{ MB}$ each (well exceeding the $50\text{ KB}$ QC threshold).
* Open sample files (`rainfall_forecast_day1.png`, `thunderstorm_warning_day1.png`) to verify color ramp fidelity, north arrow alignment, and district label legibility.

---

## 6. Troubleshooting & Operational Recovery

| Issue / Symptom | Probable Cause | Remediation Step |
| :--- | :--- | :--- |
| **`ERROR: QGIS not found`** | QGIS is installed in a non-standard directory or environment variable is missing. | Define the `IMD_QGIS_ROOT` environment variable or edit `config.py` with your exact installation path (e.g., `C:\Program Files\QGIS 3.44.14`). |
| **`Address already in use (Errno 10048)`** | Another instance of `serve_dashboard.py` or another application is bound to port 8765. | Run `open_dashboard.bat` (which automatically kills conflicting PIDs) or terminate manually via: `netstat -ano \| findstr :8765` and `taskkill /F /PID <PID>`. |
| **`QC FAIL: Output suspiciously small`** | Render canvas crashed, shapefile path invalid, or missing font library. | Ensure `data/shapefiles/District_Boundary.shp` exists. On Linux, ensure `fonts-dejavu` and `fonts-liberation` are installed (`apt install fonts-dejavu`). |
| **`PermissionError: [WinError 32]` on temporary files** | File locked by background antivirus or lingering handle. | The system implements atomic JSON replace (`atomic_json.py`) and memory joins (`join_memory_data_to_shapefile`). Ensure intermediate CSV files are not being manually generated or opened in Excel. |
| **Labels missing or distorted on Linux** | Headless display server not configured. | Ensure `Environment="QT_QPA_PLATFORM=offscreen"` is set in the systemd service file or run under `xvfb-run`. |
| **District name marked `Unknown`** | Excel sheet contains a new or misspelled district name variant. | Check `utils/excel_parser.py`. Add the spelling variation to `CANONICAL_DISTRICTS` mapping to standard 33-district attributes. |
