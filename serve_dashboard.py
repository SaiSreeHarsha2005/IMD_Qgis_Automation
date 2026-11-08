import os
import sys
import json
import time
import datetime
import subprocess
import threading
import traceback
import io
import zipfile
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
try:
    from http.server import ThreadingHTTPServer
except ImportError:
    ThreadingHTTPServer = HTTPServer

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import config

if hasattr(config, "QGIS_ROOT") and os.path.exists(config.QGIS_ROOT):
    for sp in [
        os.path.join(config.QGIS_ROOT, "apps", "Python312", "Lib", "site-packages"),
        os.path.join(config.QGIS_ROOT, "apps", "qgis-ltr", "python"),
        os.path.join(config.QGIS_ROOT, "apps", "qgis", "python"),
    ]:
        if os.path.exists(sp) and sp not in sys.path:
            sys.path.append(sp)

PORT = 8765
if len(sys.argv) > 1:
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        pass

_PIPELINE_LOCK = threading.Lock()
_PIPELINE_STATUS = {
    "running": False,
    "current_step": "Idle",
    "progress": 0,
    "module": "all",
    "last_run": None,
    "last_error": None
}

def _file_info(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {"exists": False, "size_bytes": 0, "mtime_str": "-", "mtime_epoch": 0, "age_min": -1}
    st = os.stat(filepath)
    mtime = st.st_mtime
    age_min = round((time.time() - mtime) / 60.0, 1)
    mtime_dt = datetime.datetime.fromtimestamp(mtime)
    return {
        "exists": True,
        "name": os.path.basename(filepath),
        "size_bytes": st.st_size,
        "size_kb": round(st.st_size / 1024.0, 1),
        "mtime_str": mtime_dt.strftime("%d-%b-%Y %H:%M:%S IST"),
        "mtime_epoch": mtime,
        "age_min": age_min,
    }

def get_system_telemetry() -> dict:
    input_dir = getattr(config, "INPUT_PATH", getattr(config, "CSV_PATH", os.path.join(config.PROJECT_ROOT, "data", "input")))
    output_dir = getattr(config, "OUTPUT_PATH", os.path.join(config.PROJECT_ROOT, "output"))

    excel_inputs = {}
    if os.path.exists(input_dir):
        for f in os.listdir(input_dir):
            if f.lower().endswith(".xlsx") and not f.startswith("~$"):
                fp = os.path.join(input_dir, f)
                excel_inputs[f] = _file_info(fp)

    maps = []
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            if f.endswith((".png", ".pdf", ".jpg")):
                fp = os.path.join(output_dir, f)
                info = _file_info(fp)
                cat = "Other"
                if "summary" in f:
                    cat = "5-Day Grid Summary"
                elif "thunderstorm" in f:
                    cat = "5-Day Thunderstorm Warning"
                elif "intensity" in f:
                    cat = "5-Day Rainfall Intensity"
                elif "forecast" in f or "spatial" in f:
                    cat = "7-Day Spatial Forecast"
                elif "tmax" in f or "maximum" in f:
                    cat = "Max Temperature"
                elif "tmin" in f or "minimum" in f:
                    cat = "Min Temperature"

                info["category"] = cat
                info["path"] = f"output/{f}"
                maps.append(info)

    maps.sort(key=lambda x: x["mtime_epoch"], reverse=True)

    run_status_path = os.path.join(config.LOG_PATH, "run_status.json")
    health_path = os.path.join(config.LOG_PATH, "system_health.json")

    run_status = {}
    if os.path.exists(run_status_path):
        try:
            with open(run_status_path, "r", encoding="utf-8") as f:
                run_status = json.load(f)
                if _PIPELINE_STATUS["running"]:
                    _PIPELINE_STATUS["progress"] = run_status.get("progress", _PIPELINE_STATUS["progress"])
                    _PIPELINE_STATUS["current_step"] = run_status.get("step", _PIPELINE_STATUS["current_step"])
                    _PIPELINE_STATUS["module"] = run_status.get("module", _PIPELINE_STATUS["module"])
        except Exception:
            pass

    health_status = {}
    if os.path.exists(health_path):
        try:
            with open(health_path, "r", encoding="utf-8") as f:
                health_status = json.load(f)
        except Exception:
            pass

    return {
        "timestamp": datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S IST"),
        "mode": getattr(config, "MODE", "PROD"),
        "pipeline_running": _PIPELINE_STATUS["running"],
        "pipeline_status": _PIPELINE_STATUS,
        "run_status": run_status,
        "health_status": health_status,
        "excel_inputs": excel_inputs,
        "maps": maps,
        "map_count": len(maps),
        "png_count": len([m for m in maps if m["name"].endswith(".png")]),
        "pdf_count": len([m for m in maps if m["name"].endswith(".pdf")]),
    }

def _run_pipeline_background(module="all", input_file=None):
    global _PIPELINE_STATUS
    with _PIPELINE_LOCK:
        _PIPELINE_STATUS["running"] = True
        _PIPELINE_STATUS["module"] = module
        _PIPELINE_STATUS["current_step"] = f"Initializing {module.upper()} Direct Excel Engine"
        _PIPELINE_STATUS["progress"] = 10
        _PIPELINE_STATUS["last_error"] = None

        try:
            _PIPELINE_STATUS["current_step"] = f"Generating {module.title()} Maps Directly from Excel"
            _PIPELINE_STATUS["progress"] = 25

            qgis_py = getattr(config, "QGIS_PYTHON", None)
            if not qgis_py or not os.path.exists(qgis_py):
                cand = os.path.join(config.QGIS_ROOT, "bin", "python-qgis-ltr.bat")
                qgis_py = cand if os.path.exists(cand) else os.path.join(config.QGIS_ROOT, "bin", "python-qgis.bat")
            script_path = os.path.join(config.PROJECT_ROOT, "scripts", "imd_automation.py")

            cmd = [qgis_py if os.path.exists(qgis_py) else sys.executable, script_path, f"--module={module}"]
            if input_file:
                cmd.append(f"--input={input_file}")

            res = subprocess.run(cmd, cwd=config.PROJECT_ROOT, capture_output=True, text=True)

            if res.returncode == 0:
                _PIPELINE_STATUS["current_step"] = "Completed Successfully"
                _PIPELINE_STATUS["progress"] = 100
                _PIPELINE_STATUS["last_run"] = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")
            else:
                _PIPELINE_STATUS["current_step"] = "Failed"
                _PIPELINE_STATUS["progress"] = 0
                _PIPELINE_STATUS["last_error"] = res.stderr or res.stdout
        except Exception as e:
            _PIPELINE_STATUS["current_step"] = f"Failed: {str(e)}"
            _PIPELINE_STATUS["progress"] = 0
            _PIPELINE_STATUS["last_error"] = str(e)
        finally:
            _PIPELINE_STATUS["running"] = False

class OperationalDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=config.PROJECT_ROOT, **kwargs)

    def send_json_response(self, code: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/status"):
            try:
                telemetry = get_system_telemetry()
                self.send_json_response(200, telemetry)
            except Exception as e:
                self.send_json_response(200, {"success": False, "error": str(e)})
            return

        if self.path.startswith("/api/download_all") or self.path.startswith("/api/download_all_png") or self.path.startswith("/api/download_all_pdf"):
            try:
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                dl_type = params.get("type", params.get("format", ["all"]))[0].lower()

                if "download_all_png" in parsed.path:
                    dl_type = "png"
                elif "download_all_pdf" in parsed.path:
                    dl_type = "pdf"

                output_dir = getattr(config, "OUTPUT_PATH", os.path.join(config.PROJECT_ROOT, "output"))
                if not os.path.exists(output_dir):
                    self.send_json_response(404, {"success": False, "message": "Output directory not found."})
                    return

                if dl_type == "png":
                    valid_exts = (".png", ".jpg", ".jpeg")
                    prefix = "IMD_Hyderabad_Maps_PNG"
                    compression = zipfile.ZIP_STORED
                elif dl_type == "pdf":
                    valid_exts = (".pdf",)
                    prefix = "IMD_Hyderabad_Bulletins_PDF"
                    compression = zipfile.ZIP_DEFLATED
                else:
                    valid_exts = (".png", ".jpg", ".jpeg", ".pdf")
                    prefix = "IMD_Hyderabad_All_Maps"
                    compression = zipfile.ZIP_DEFLATED

                files_to_zip = []
                for f in sorted(os.listdir(output_dir)):
                    if f.lower().endswith(valid_exts):
                        fp = os.path.join(output_dir, f)
                        if os.path.isfile(fp):
                            files_to_zip.append((fp, f))

                if not files_to_zip:
                    self.send_json_response(404, {
                        "success": False,
                        "message": f"No {dl_type.upper()} map files found in output directory to download."
                    })
                    return

                ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_filename = f"{prefix}_{ts_str}.zip"

                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", compression=compression) as zf:
                    for full_path, arc_name in files_to_zip:
                        zf.write(full_path, arcname=arc_name)

                zip_data = buf.getvalue()

                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f'attachment; filename="{zip_filename}"')
                self.send_header("Content-Length", str(len(zip_data)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(zip_data)
                print(f"  [DOWNLOAD OK] Served {zip_filename} ({len(zip_data)} bytes, {len(files_to_zip)} files) to {self.client_address[0]}")
                return
            except Exception as e:
                err_msg = f"Error generating batch download: {str(e)}"
                print(f"  [ERROR] {err_msg}")
                traceback.print_exc()
                self.send_json_response(500, {"success": False, "message": err_msg})
                return

        # Clean URL: Serve dashboard directly on root path without exposing /templates/dashboard.html
        if self.path == "/" or self.path == "/index.html" or self.path.startswith("/?"):
            dash_path = os.path.join(config.PROJECT_ROOT, "templates", "dashboard.html")
            if os.path.exists(dash_path):
                with open(dash_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(content)
                return

        # Hide /templates/dashboard.html if accessed directly, redirecting cleanly to root
        if self.path == "/templates/dashboard.html" or self.path.startswith("/templates/dashboard.html?"):
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path == "/favicon.ico":
            self.send_response(302)
            self.send_header("Location", "/templates/IMD_LOGO.png")
            self.end_headers()
            return

        if self.path == "/IMD_LOGO.png":
            self.send_response(302)
            self.send_header("Location", "/templates/IMD_LOGO.png")
            self.end_headers()
            return

        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/parse_excel"):
            try:
                from utils.excel_parser import parse_any_excel_memory
                input_dir = getattr(config, "INPUT_PATH", getattr(config, "CSV_PATH", os.path.join(config.PROJECT_ROOT, "data", "input")))
                verified = []
                if os.path.exists(input_dir):
                    for f in os.listdir(input_dir):
                        if f.lower().endswith(".xlsx") and not f.startswith("~$"):
                            res = parse_any_excel_memory(os.path.join(input_dir, f))
                            verified.append(f"{f} ({len(res.get('districts', []))} districts)")

                if verified:
                    msg = f"Direct Excel Engine: Verified in-memory parsing for: {', '.join(verified)}. Ready for direct map generation without intermediate CSVs."
                else:
                    msg = "No .xlsx files found in data directory."

                self.send_json_response(200, {"success": True, "message": msg, "files": verified})
                return
            except Exception as e:
                err_msg = f"Excel parse verification error: {str(e)}"
                print(f"  [ERROR] {err_msg}")
                traceback.print_exc()
                self.send_json_response(200, {"success": False, "message": err_msg, "error": str(e)})
                return

        elif self.path.startswith("/api/run_rain_pipeline"):
            try:
                if _PIPELINE_STATUS["running"]:
                    self.send_json_response(200, {
                        "success": False,
                        "message": f"A pipeline ({_PIPELINE_STATUS.get('module', 'all').upper()}) is already running in the background!"
                    })
                    return

                t = threading.Thread(target=_run_pipeline_background, args=("rain",), daemon=True)
                t.start()

                self.send_json_response(200, {
                    "success": True,
                    "message": "Rainfall Map Generation Pipeline started in the background."
                })
                return
            except Exception as e:
                err_msg = f"Rain maps pipeline launch error: {str(e)}"
                print(f"  [ERROR] {err_msg}")
                traceback.print_exc()
                self.send_json_response(200, {"success": False, "message": err_msg, "error": str(e)})
                return

        elif self.path.startswith("/api/run_summer_pipeline"):
            try:
                if _PIPELINE_STATUS["running"]:
                    self.send_json_response(200, {
                        "success": False,
                        "message": f"A pipeline ({_PIPELINE_STATUS.get('module', 'all').upper()}) is already running in the background!"
                    })
                    return

                t = threading.Thread(target=_run_pipeline_background, args=("summer",), daemon=True)
                t.start()

                self.send_json_response(200, {
                    "success": True,
                    "message": "Summer Temperature Map Generation Pipeline started in the background."
                })
                return
            except Exception as e:
                err_msg = f"Summer maps pipeline launch error: {str(e)}"
                print(f"  [ERROR] {err_msg}")
                traceback.print_exc()
                self.send_json_response(200, {"success": False, "message": err_msg, "error": str(e)})
                return

        elif self.path.startswith("/api/run_pipeline"):
            try:
                if _PIPELINE_STATUS["running"]:
                    self.send_json_response(200, {
                        "success": False,
                        "message": f"A pipeline ({_PIPELINE_STATUS.get('module', 'all').upper()}) is already running in the background!"
                    })
                    return

                module_param = "all"
                if "module=rain" in self.path:
                    module_param = "rain"
                elif "module=summer" in self.path:
                    module_param = "summer"

                t = threading.Thread(target=_run_pipeline_background, args=(module_param,), daemon=True)
                t.start()

                self.send_json_response(200, {
                    "success": True,
                    "message": f"QGIS Map Generation Pipeline [{module_param.upper()}] started in the background!"
                })
                return
            except Exception as e:
                err_msg = f"Pipeline execution launch error: {str(e)}"
                print(f"  [ERROR] {err_msg}")
                traceback.print_exc()
                self.send_json_response(200, {"success": False, "message": err_msg, "error": str(e)})
                return

        elif self.path.startswith("/api/upload"):
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length)
                content_type = self.headers.get("Content-Type", "")

                saved_files = []
                import re
                if "multipart/form-data" in content_type:
                    b_match = re.search(r'boundary=([^;]+)', content_type, re.IGNORECASE)
                    if b_match:
                        boundary_str = b_match.group(1).strip().strip('"').strip("'")
                        boundary = boundary_str.encode("utf-8")
                        parts = body_bytes.split(b"--" + boundary)
                        for part in parts:
                            if b"filename=" in part:
                                if b"\r\n\r\n" in part:
                                    headers_part, data_part = part.split(b"\r\n\r\n", 1)
                                elif b"\n\n" in part:
                                    headers_part, data_part = part.split(b"\n\n", 1)
                                else:
                                    continue

                                if data_part.endswith(b"--\r\n"):
                                    data_part = data_part[:-4]
                                elif data_part.endswith(b"\r\n"):
                                    data_part = data_part[:-2]
                                elif data_part.endswith(b"\n"):
                                    data_part = data_part[:-1]
                                if data_part.endswith(b"--"):
                                    data_part = data_part[:-2]
                                if data_part.endswith(b"\r\n"):
                                    data_part = data_part[:-2]

                                headers_str = headers_part.decode("utf-8", "ignore")
                                fn_match = re.search(r'filename=["\']?([^"\';\r\n]+)["\']?', headers_str)
                                fname = fn_match.group(1) if fn_match else "uploaded_workbook.xlsx"
                                fname = os.path.basename(fname.strip())
                                if not fname.lower().endswith(".xlsx"):
                                    fname += ".xlsx"

                                upload_dir = getattr(config, "INPUT_PATH", getattr(config, "CSV_PATH", os.path.join(config.PROJECT_ROOT, "data", "input")))
                                os.makedirs(upload_dir, exist_ok=True)
                                out_path = os.path.join(upload_dir, fname)
                                with open(out_path, "wb") as f:
                                    f.write(data_part)
                                saved_files.append(fname)
                                print(f"  [UPLOAD OK] Saved {fname} ({len(data_part)} bytes) to {upload_dir}")

                if saved_files:
                    msg = f"Successfully uploaded and saved {len(saved_files)} file(s): {', '.join(saved_files)}"
                    self.send_json_response(200, {"success": True, "message": msg, "files": saved_files})
                else:
                    self.send_json_response(200, {"success": False, "message": "No valid .xlsx file data was extracted from upload payload."})
                return
            except Exception as e:
                err_msg = f"Upload error: {str(e)}"
                print(f"  [ERROR] {err_msg}")
                traceback.print_exc()
                self.send_json_response(200, {"success": False, "message": err_msg, "error": str(e)})
                return

        elif self.path.startswith("/api/delete_workbook"):
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                fname = params.get("file", [None])[0]
                if not fname:
                    self.send_json_response(200, {"success": False, "message": "No file parameter provided."})
                    return

                fname = os.path.basename(fname)
                upload_dir = getattr(config, "INPUT_PATH", getattr(config, "CSV_PATH", os.path.join(config.PROJECT_ROOT, "data", "input")))
                target_fp = os.path.join(upload_dir, fname)
                if os.path.exists(target_fp):
                    os.remove(target_fp)
                    self.send_json_response(200, {"success": True, "message": f"Deleted {fname} from input directory."})
                else:
                    self.send_json_response(200, {"success": False, "message": f"File {fname} not found in input directory."})
                return
            except Exception as e:
                self.send_json_response(200, {"success": False, "message": f"Delete error: {str(e)}"})
                return

        self.send_json_response(200, {"success": False, "message": f"Unknown API endpoint: {self.path}"})

class ReusableThreadingServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server():
    global PORT
    httpd = None
    for try_port in [PORT, 8766, 8767, 8768, 8769]:
        try:
            server_address = ("0.0.0.0", try_port)
            httpd = ReusableThreadingServer(server_address, OperationalDashboardHandler)
            PORT = try_port
            break
        except OSError:
            continue

    if not httpd:
        print("  [SERVER ERROR] Could not bind to any port in range 8765-8769.")
        sys.exit(1)

    print(f"  [SERVER OK] Serving IMD Operational Dashboard on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  [SERVER STOP] Dashboard server stopped.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
