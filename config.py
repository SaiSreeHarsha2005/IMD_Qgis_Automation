import os
import sys

try:
    _THIS_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _THIS_DIR = os.path.abspath(os.getcwd())

PROJECT_ROOT = _THIS_DIR
IS_LINUX = os.name != "nt"

def _detect_qgis_root() -> str:
    if IS_LINUX:
        return os.environ.get("IMD_QGIS_ROOT", "/usr")
    env_root = os.environ.get("IMD_QGIS_ROOT") or os.environ.get("QGIS_ROOT")
    if env_root and os.path.isdir(env_root):
        return env_root
    prefix = os.environ.get("QGIS_PREFIX_PATH")
    if prefix:
        cand = os.path.abspath(os.path.join(prefix, "..", ".."))
        if os.path.isdir(cand) and os.path.exists(os.path.join(cand, "bin")):
            return cand
    import glob
    candidates = []
    for pattern in [r"C:\Program Files\QGIS*", r"C:\Program Files (x86)\QGIS*", r"C:\OSGeo4W*"]:
        candidates.extend(glob.glob(pattern))
    candidates.sort(reverse=True)
    for c in candidates:
        if os.path.isdir(c) and os.path.exists(os.path.join(c, "bin")):
            return c
    return r"C:\Program Files\QGIS 3.44.14"

QGIS_ROOT = _detect_qgis_root()

def _detect_qgis_prefix(root: str) -> str:
    if IS_LINUX:
        return os.environ.get("QGIS_PREFIX_PATH", "/usr")
    env_prefix = os.environ.get("QGIS_PREFIX_PATH")
    if env_prefix and os.path.isdir(env_prefix):
        return env_prefix
    for sub in ["qgis-ltr", "qgis"]:
        cand = os.path.join(root, "apps", sub)
        if os.path.isdir(cand):
            return cand
    return root

QGIS_PREFIX = _detect_qgis_prefix(QGIS_ROOT)

def _detect_qgis_python(root: str) -> str:
    if IS_LINUX:
        return sys.executable
    env_py = os.environ.get("QGIS_PYTHON")
    if env_py and os.path.exists(env_py):
        return env_py
    candidates = [
        os.path.join(root, "bin", "python-qgis-ltr.bat"),
        os.path.join(root, "bin", "python-qgis.bat"),
        os.path.join(root, "bin", "python3.exe"),
        os.path.join(root, "bin", "python.exe"),
        os.path.join(root, "apps", "Python312", "python.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return sys.executable

QGIS_PYTHON = _detect_qgis_python(QGIS_ROOT)

MODE = "PROD"

ENABLE_VECTOR = True
EXPORT_PNG = True
EXPORT_PDF = True
EXPORT_DPI = 300

STRICT_DISTRICT_MATCH = True
RF_CLAMP_MIN = 0.0
RF_CLAMP_MAX = 1000.0

LOG_ROTATION_DAYS = 14
LOG_MAX_BYTES = 5_000_000

CRS_EPSG = "EPSG:4326"
NORTH_ARROW_STYLE = 4
BUFFER_FRACTION = 0.01

SHAPEFILE_PATH = os.path.join(PROJECT_ROOT, "data", "shapefiles")
INPUT_PATH = os.path.join(PROJECT_ROOT, "data", "input")
CSV_PATH = INPUT_PATH
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "templates")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "output")
LOG_PATH = os.path.join(PROJECT_ROOT, "logs")
SCRIPTS_PATH = os.path.join(PROJECT_ROOT, "scripts")

_arrow_candidates = [
    os.path.join(TEMPLATE_PATH, "symbols", f"NorthArrow_0{NORTH_ARROW_STYLE}.svg"),
    os.path.join(QGIS_PREFIX, "svg", "arrows", f"NorthArrow_0{NORTH_ARROW_STYLE}.svg"),
    os.path.join(QGIS_ROOT, "apps", "qgis-ltr", "svg", "arrows", f"NorthArrow_0{NORTH_ARROW_STYLE}.svg"),
    os.path.join(QGIS_ROOT, "apps", "qgis", "svg", "arrows", f"NorthArrow_0{NORTH_ARROW_STYLE}.svg"),
    f"/usr/share/qgis/svg/arrows/NorthArrow_0{NORTH_ARROW_STYLE}.svg",
    f"/usr/share/qgis/svg/NorthArrow_0{NORTH_ARROW_STYLE}.svg",
]
NORTH_ARROW_SVG = next((p for p in _arrow_candidates if os.path.exists(p)), _arrow_candidates[0])

def get_strict_match() -> bool:
    return STRICT_DISTRICT_MATCH and (MODE == "PROD")

def get_max_data_age_minutes() -> float:
    return 120.0 if MODE == "PROD" else 9999.0

def _check() -> None:
    errors = []
    warnings = []

    dir_checks = [
        ("SHAPEFILE_PATH", SHAPEFILE_PATH),
        ("INPUT_PATH", INPUT_PATH),
        ("TEMPLATE_PATH", TEMPLATE_PATH),
        ("OUTPUT_PATH", OUTPUT_PATH),
    ]
    for label, path in dir_checks:
        if not os.path.isdir(path):
            warnings.append(f"{label} not found: {path}")

    try:
        os.makedirs(LOG_PATH, exist_ok=True)
    except OSError as exc:
        warnings.append(f"Cannot create LOG_PATH={LOG_PATH}: {exc}")

    if not IS_LINUX:
        if not os.path.isdir(QGIS_ROOT):
            errors.append(f"QGIS_ROOT not found: {QGIS_ROOT}")
        elif not os.path.exists(QGIS_PYTHON):
            errors.append(f"QGIS Python executable not found under {QGIS_ROOT}\\bin\\")

    if not os.path.exists(NORTH_ARROW_SVG):
        warnings.append(f"North arrow SVG not found at: {NORTH_ARROW_SVG}")

    if MODE not in ("PROD", "DEV"):
        warnings.append(f"MODE='{MODE}' is not 'PROD' or 'DEV'")

    for msg in warnings:
        print(f"  [CONFIG WARN]  {msg}")
    for msg in errors:
        print(f"  [CONFIG ERROR] {msg}")

    if not errors and not warnings:
        print(f"  [CONFIG OK]  PROJECT_ROOT={PROJECT_ROOT}  MODE={MODE}  QGIS={QGIS_ROOT}  PYTHON={os.path.basename(QGIS_PYTHON)}")

_check()
