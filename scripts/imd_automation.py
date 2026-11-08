import os
import sys
import math
import re
import time
import json
import datetime
import traceback
import shutil
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from osgeo import gdal
    gdal.PushErrorHandler('CPLQuietErrorHandler')
except ImportError:
    pass

try:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = os.path.join(os.path.abspath(os.getcwd()), "scripts")

_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import config

try:
    _UTILS_DIR = os.path.join(_PROJECT_ROOT, "utils")
    if _UTILS_DIR not in sys.path:
        sys.path.insert(0, _UTILS_DIR)
    from utils.atomic_json import atomic_write_json, read_json_safe
except ImportError:
    import json as _json
    def atomic_write_json(path, data, indent=2):
        tmp = path + ".tmp"
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                _json.dump(data, f, indent=indent, default=str)
            os.replace(tmp, path)
            return True
        except Exception:
            try:
                os.remove(tmp)
            except Exception:
                pass
            return False
    def read_json_safe(path, default=None):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return _json.load(f)
        except Exception:
            return default if default is not None else {}

_qgs_app = None
_QGIS_INITIALIZED = False

try:
    from qgis.core import QgsApplication
    if not QgsApplication.instance():
        from qgis.analysis import QgsNativeAlgorithms
        QGIS_PREFIX = getattr(config, "QGIS_PREFIX", os.environ.get(
            "QGIS_PREFIX_PATH",
            os.path.join(config.QGIS_ROOT, "apps", "qgis")
        ))
        QgsApplication.setPrefixPath(QGIS_PREFIX, True)
        _qgs_app = QgsApplication([], False)
        _qgs_app.initQgis()
        plugin_path = os.path.join(QGIS_PREFIX, "python", "plugins")
        if plugin_path not in sys.path:
            sys.path.append(plugin_path)
        import processing
        from processing.core.Processing import Processing
        Processing.initialize()
        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
        _QGIS_INITIALIZED = True
    else:
        import processing
except ImportError:
    import processing

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsPrintLayout,
    QgsLayoutExporter,
    QgsLayoutItemMap,
    QgsLayoutItemLegend,
    QgsLayoutItemLabel,
    QgsLayoutItemPicture,
    QgsLayoutItemShape,
    QgsLayoutItemScaleBar,
    QgsLayoutSize,
    QgsLayoutPoint,
    QgsUnitTypes,
    QgsRectangle,
    QgsGraduatedSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsRendererRange,
    QgsFillSymbol,
    QgsMarkerSymbol,
    QgsSvgMarkerSymbolLayer,
    QgsLineSymbol,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
    QgsCoordinateReferenceSystem,
    QgsLayoutMeasurement,
    QgsSingleSymbolRenderer,
    QgsProperty,
    QgsPointXY,
    QgsGeometry,
    QgsFeature,
    QgsField,
    QgsVectorFileWriter,
)

try:
    from qgis.core import QgsLegendStyle
except ImportError:
    QgsLegendStyle = None

try:
    from qgis.core import (
        QgsLayerTree,
        QgsLayerTreeLayer,
        QgsLayerTreeGroup,
        QgsLayerTreeModel,
    )
    _HAS_LEGEND_MODEL = True
except ImportError:
    _HAS_LEGEND_MODEL = False

from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import Qt, QVariant

MM = QgsUnitTypes.LayoutMillimeters

PATHS = {
    "district_shp"      : os.path.join(config.SHAPEFILE_PATH, "District_Boundary.shp"),
    "spatial_csv"       : os.path.join(config.CSV_PATH,       "5day_spatial.csv"),
    "intensity_csv"     : os.path.join(config.CSV_PATH,       "5day_intensity.csv"),
    "warning_csv"       : os.path.join(config.CSV_PATH,       "5day_warning.csv"),
    "temp_csv"          : os.path.join(config.CSV_PATH,       "temp_data.csv"),
    "rf_stn_csv"        : os.path.join(config.CSV_PATH,       "rf_stn.csv"),
    "realised_csv"      : os.path.join(config.CSV_PATH,       "realised_rainfall.csv"),
    "imd_logo"          : os.path.join(config.TEMPLATE_PATH,  "IMD_LOGO.png"),
    "north_arrow_svg"   : getattr(config, "NORTH_ARROW_SVG", os.path.join(
        config.QGIS_ROOT, "apps", "qgis", "svg", "arrows",
        f"NorthArrow_0{config.NORTH_ARROW_STYLE}.svg"
    )),
    "output_folder"     : config.OUTPUT_PATH + os.sep,
    "log_folder"        : config.LOG_PATH,
    "run_log_json"      : os.path.join(config.LOG_PATH, "run_status.json"),
    "system_health"     : os.path.join(config.LOG_PATH, "system_health.json"),
    "fallback_spatial"  : os.path.join(config.LOG_PATH, "fallback_spatial.csv"),
}

NORTH_ARROW_SVG = PATHS["north_arrow_svg"]

MAX_DATA_AGE_MINUTES = config.get_max_data_age_minutes()
EXPORT_PNG           = config.EXPORT_PNG
EXPORT_PDF           = config.EXPORT_PDF
PNG_DPI              = config.EXPORT_DPI
SPATIAL_DAYS         = [1, 2, 3, 4, 5, 6, 7]
WARNING_DAYS         = [1, 2, 3, 4, 5]
FORECAST_DAYS        = [1, 2, 3, 4, 5]
SHP_NAME_FIELD       = "Dist_Name"
MIN_OUTPUT_KB        = 50

TELANGANA_EXTENT = QgsRectangle(
    76.82931912330009, 15.78465826496774,
    81.72454377570009, 19.96864850203235
)

PAGE_W, PAGE_H = 297.0, 210.0

LOGO_X,     LOGO_Y,     LOGO_W,    LOGO_H    = 12.0,  4.0, 22.0, 22.0
LOGO_LBL_X, LOGO_LBL_Y, LOGO_LBL_W, LOGO_LBL_H =  0.0, 26.5, 46.0, 11.0

NORTH_X, NORTH_Y, NORTH_W, NORTH_H = 266.0, 4.0, 16.0, 18.0
NORTH_LBL_X, NORTH_LBL_Y, NORTH_LBL_W, NORTH_LBL_H = 266.0, 22.5, 16.0, 5.0

TITLE_X, TITLE_Y, TITLE_W, TITLE_H = 48.0, 6.0, 202.0, 14.0
MAP_X, MAP_Y, MAP_W, MAP_H = 10.0, 24.0, 215.0, 170.0
LEGEND_X, LEGEND_Y, LEGEND_W, LEGEND_H = 230.0, 55.0, 58.0, 100.0
SCALEBAR_X, SCALEBAR_Y, SCALEBAR_W, SCALEBAR_H = 8.0, 185.0, 70.0, 6.0
FOOTER_X, FOOTER_Y, FOOTER_W, FOOTER_H = 5.0, 204.0, 287.0, 5.0

FOOTER_TEXT = (
    "India Meteorological Department — Meteorological Centre Hyderabad  |  "
    "Ph: 040-27908506  |  Website: mausam.imd.gov.in/hyderabad"
)

SPATIAL_CATEGORIES = [
    {"lower": 0.5, "upper": 1.5, "label": "Dry",               "color": "#FFFFFF"},
    {"lower": 1.5, "upper": 2.5, "label": "One or two places", "color": "#6BEA48"},
    {"lower": 2.5, "upper": 3.5, "label": "Few places",        "color": "#0A7A32"},
    {"lower": 3.5, "upper": 4.5, "label": "Many places",       "color": "#56ACE6"},
    {"lower": 4.5, "upper": 5.5, "label": "Most places",       "color": "#2E73D8"},
]

RAIN_WARNING_CATEGORIES = [
    {"lower": 0.5, "upper": 1.5, "label": "No warning(No action)", "color": "#009900"},
    {"lower": 1.5, "upper": 2.5, "label": "Watch(Be updated)",     "color": "#FFFF00"},
    {"lower": 2.5, "upper": 3.5, "label": "Alert(Be prepared)",    "color": "#FF9900"},
    {"lower": 3.5, "upper": 99.5, "label": "Warning(Take action)",  "color": "#FF0000"},
]

TMAX_CATEGORIES = [
    {"lower":  0, "upper": 40, "label": "No Warning (≤ 40 °C)",     "color": "#2E7D32"},
    {"lower": 40, "upper": 45, "label": "Be Alert (41–45 °C)",      "color": "#FFD54F"},
    {"lower": 45, "upper": 47, "label": "Be Prepared (46–47 °C)",   "color": "#FB8C00"},
    {"lower": 47, "upper": 99, "label": "Warning (> 47 °C)",        "color": "#D32F2F"},
]

TMIN_CATEGORIES = [
    {"lower": -99, "upper":  5, "label": "Warning (< 5 °C)",        "color": "#D32F2F"},
    {"lower":   5, "upper": 11, "label": "Alert (5–10 °C)",         "color": "#FB8C00"},
    {"lower":  11, "upper": 15, "label": "Watch (11–15 °C)",        "color": "#FFD54F"},
    {"lower":  15, "upper": 99, "label": "No Warning (> 15 °C)",    "color": "#2E7D32"},
]

RAINFALL_LEGEND_CATEGORIES = [
    {"label": "No Rain",                               "color": "#FFFFFF"},
    {"label": "Very Light Rain(0.1-2.4)",              "color": "#ADFF2F"},
    {"label": "Light Rain(2.5-15.5)",                  "color": "#00C800"},
    {"label": "Moderate Rain(15.6-64.4)",              "color": "#00BFFF"},
    {"label": "Heavy Rain(64.5-115.5)",                "color": "#FFD700"},
    {"label": "Very Heavy Rain(115.6-204.4)",          "color": "#FF8C00"},
    {"label": "Extremely Heavy Rain(more than 204.4)", "color": "#FF0000"},
]

RAINFALL_DISTRICT_CONFIG = {
    "Adilabad":                {"lx": 78.565, "ly": 19.580, "sx": 78.565, "sy": 19.460, "size": 7.5},
    "Bhadradri Kothagudem":    {"lx": 80.600, "ly": 17.800, "sx": 80.600, "sy": 17.650, "size": 7.8},
    "Hanumakonda":             {"lx": 79.480, "ly": 18.065, "sx": 79.480, "sy": 17.980, "size": 5.2},
    "Hyderabad":               {"lx": 78.470, "ly": 17.415, "sx": 78.470, "sy": 17.365, "size": 4.2},
    "Jagtial":                 {"lx": 78.860, "ly": 18.880, "sx": 78.860, "sy": 18.760, "size": 7.2},
    "Jangoan":                 {"lx": 79.260, "ly": 17.810, "sx": 79.260, "sy": 17.700, "size": 6.8},
    "Jayashankar Bhupalpally": {"lx": 79.950, "ly": 18.580, "sx": 79.950, "sy": 18.460, "size": 7.2},
    "Jogulamba Gadwal":        {"lx": 77.740, "ly": 16.150, "sx": 77.740, "sy": 16.030, "size": 6.8},
    "Kamareddy":               {"lx": 78.050, "ly": 18.350, "sx": 78.050, "sy": 18.230, "size": 7.2},
    "Karimnagar":              {"lx": 79.280, "ly": 18.350, "sx": 79.280, "sy": 18.240, "size": 6.8},
    "Khammam":                 {"lx": 80.300, "ly": 17.260, "sx": 80.300, "sy": 17.150, "size": 7.2},
    "Kumurambheem Asifabad":   {"lx": 79.600, "ly": 19.420, "sx": 79.600, "sy": 19.300, "size": 7.5},
    "Mahabubabad":             {"lx": 80.000, "ly": 17.650, "sx": 80.000, "sy": 17.530, "size": 7.2},
    "Mahabubnagar":            {"lx": 77.950, "ly": 16.800, "sx": 77.950, "sy": 16.680, "size": 7.5},
    "Mancherial":              {"lx": 79.600, "ly": 19.040, "sx": 79.600, "sy": 18.920, "size": 7.2},
    "Medak":                   {"lx": 78.300, "ly": 18.000, "sx": 78.300, "sy": 17.880, "size": 7.0},
    "Medchal Malkajgiri":      {"lx": 78.570, "ly": 17.590, "sx": 78.570, "sy": 17.510, "size": 4.8},
    "Mulugu":                  {"lx": 80.400, "ly": 18.380, "sx": 80.400, "sy": 18.250, "size": 7.5},
    "Nagarkurnool":            {"lx": 78.550, "ly": 16.380, "sx": 78.550, "sy": 16.250, "size": 7.5},
    "Nalgonda":                {"lx": 79.220, "ly": 16.960, "sx": 79.220, "sy": 16.820, "size": 7.5},
    "Narayanpet":              {"lx": 77.580, "ly": 16.600, "sx": 77.580, "sy": 16.480, "size": 6.5},
    "Nirmal":                  {"lx": 78.180, "ly": 19.140, "sx": 78.180, "sy": 19.030, "size": 7.0},
    "Nizamabad":               {"lx": 78.260, "ly": 18.760, "sx": 78.260, "sy": 18.640, "size": 7.2},
    "Peddapalli":              {"lx": 79.460, "ly": 18.660, "sx": 79.460, "sy": 18.550, "size": 7.0},
    "Rajanna Sircilla":        {"lx": 78.750, "ly": 18.470, "sx": 78.750, "sy": 18.370, "size": 6.2},
    "Rangareddy":              {"lx": 78.440, "ly": 17.150, "sx": 78.440, "sy": 17.030, "size": 7.2},
    "Sangareddy":              {"lx": 77.780, "ly": 17.820, "sx": 77.780, "sy": 17.700, "size": 7.2},
    "Siddipet":                {"lx": 78.820, "ly": 18.060, "sx": 78.820, "sy": 17.940, "size": 7.2},
    "Suryapet":                {"lx": 79.790, "ly": 17.060, "sx": 79.790, "sy": 16.940, "size": 7.2},
    "Vikarabad":               {"lx": 77.760, "ly": 17.320, "sx": 77.760, "sy": 17.200, "size": 7.2},
    "Wanaparthy":              {"lx": 78.020, "ly": 16.360, "sx": 78.020, "sy": 16.250, "size": 6.5},
    "Warangal":                {"lx": 79.780, "ly": 17.980, "sx": 79.780, "sy": 17.890, "size": 5.4},
    "Yadadri Bhuvanagiri":     {"lx": 78.980, "ly": 17.530, "sx": 78.980, "sy": 17.410, "size": 7.2},
}

def log(msg, level="INFO"):
    icons = {
        "INFO" : "[OK]  ",
        "WARN" : "[WARN]",
        "ERROR": "[ERR] ",
        "STEP" : "[STEP]",
    }
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}]  {icons.get(level, '      ')}  {msg}")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        log(f"Created folder: {path}")

def delete_file_safe(path):
    if os.path.exists(path):
        try:
            os.remove(path)
        except PermissionError:
            log(f"File locked, skipping delete: {os.path.basename(path)}", "WARN")

def remove_all_layers(project):
    try:
        project.clear()
        log("Cleared QGIS project via project.clear()")
    except Exception as e:
        log(f"project.clear() warning ({e}) — falling back to manual removal", "WARN")
        try:
            for lyr_id in list(project.mapLayers().keys()):
                try:
                    project.removeMapLayer(lyr_id)
                except Exception:
                    pass
        except Exception as e2:
            log(f"Layer clear fallback warning: {e2}", "WARN")

def move_resize(item, x, y, w, h):
    item.attemptMove(QgsLayoutPoint(x, y, MM), True, False, 0)
    item.attemptResize(QgsLayoutSize(w, h, MM))

def day_date_str(day):
    return (datetime.datetime.now() + datetime.timedelta(days=day - 1)).strftime("%d-%m-%Y")

def today_date_str():
    return datetime.datetime.now().strftime("%d-%m-%Y")

def quality_check_output_strict(path, min_kb=None):
    min_kb = min_kb or MIN_OUTPUT_KB
    if not os.path.exists(path):
        raise Exception(f"[QC FAIL] Output file missing: {path}")
    size_kb = os.path.getsize(path) / 1024
    if size_kb < min_kb:
        raise Exception(
            f"[QC FAIL] Output suspiciously small ({size_kb:.1f} KB < {min_kb} KB): "
            f"{os.path.basename(path)}"
        )
    log(f"[QC OK] {os.path.basename(path)}  ({size_kb:.0f} KB)")

def write_run_log(status, png_count, errors, start, end=None, estimated=False, progress=0, step="", module="all"):
    try:
        ensure_dir(PATHS["log_folder"])
        now = end or datetime.datetime.now()
        data = {
            "status"         : status,
            "module"         : module,
            "progress"       : progress,
            "step"           : step,
            "last_run"       : start.strftime("%d-%m-%Y %H:%M:%S"),
            "end_time"       : now.strftime("%d-%m-%Y %H:%M:%S"),
            "maps_generated" : png_count,
            "is_estimated"   : estimated,
            "mode"           : config.MODE,
            "errors"         : errors,
            "date"           : start.strftime("%d-%m-%Y"),
            "start"          : start.isoformat(),
            "end"            : now.isoformat(),
            "elapsed_s"      : (now - start).seconds,
            "png_count"      : png_count,
        }
        atomic_write_json(PATHS["run_log_json"], data)
    except Exception as e:
        log(f"run_log write warning: {e}", "WARN")

def write_system_health(status: str, message: str = "") -> None:
    try:
        data = {
            "status": status,
            "message": message,
            "timestamp": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        }
        atomic_write_json(PATHS["system_health"], data)
    except Exception:
        pass

def send_alert(subject: str, message: str) -> None:
    pass

def join_memory_data_to_shapefile(district_layer, districts_data, shp_name_field, data_fields, output_gpkg):
    from utils.excel_parser import _normalize_name, CANONICAL_DISTRICTS

    dist_map = {}
    for d in districts_data:
        k = _normalize_name(d.get("District", ""))
        canonical_info = CANONICAL_DISTRICTS.get(k)
        if canonical_info:
            dist_map[_normalize_name(canonical_info[0])] = d
        dist_map[k] = d

    if os.path.exists(output_gpkg):
        delete_file_safe(output_gpkg)
    if os.path.exists(output_gpkg):
        output_gpkg = output_gpkg.replace(".gpkg", f"_{int(time.time())}.gpkg")

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = "districts"
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

    QgsVectorFileWriter.writeAsVectorFormatV3(
        district_layer, output_gpkg, district_layer.transformContext(), options
    )

    out_lyr = QgsVectorLayer(output_gpkg, "JoinedLayer", "ogr")
    if not out_lyr.isValid():
        raise RuntimeError(f"Created GPKG layer is invalid: {output_gpkg}")

    new_fields = []
    for fld in data_fields:
        if any(p in fld for p in ("tmax", "tmin", "temp", "lat", "long")):
            new_fields.append(QgsField(fld, QVariant.Double))
        else:
            new_fields.append(QgsField(fld, QVariant.Int))

    out_lyr.startEditing()
    out_lyr.dataProvider().addAttributes(new_fields)
    out_lyr.updateFields()

    for feat in out_lyr.getFeatures():
        dist_val = str(feat[shp_name_field] or "").strip()
        norm = _normalize_name(dist_val)
        m_data = dist_map.get(norm, {})

        for fld in data_fields:
            if fld in m_data:
                val = m_data[fld]
                feat[fld] = float(val) if any(p in fld for p in ("tmax", "tmin", "temp")) else int(val)
            else:
                feat[fld] = 0.0 if any(p in fld for p in ("tmax", "tmin", "temp")) else 0
        out_lyr.updateFeature(feat)

    out_lyr.commitChanges()
    fc = out_lyr.featureCount()
    out_lyr = None
    import gc
    gc.collect()
    time.sleep(0.2)
    log(f"In-Memory Join complete: {fc} features populated in {os.path.basename(output_gpkg)}")
    return output_gpkg

def apply_graduated_fill(layer, field, categories):
    ranges = []
    for cat in categories:
        sym = QgsFillSymbol.createSimple({
            "color"             : cat["color"],
            "outline_color"     : "0,0,0,255",
            "outline_style"     : "solid",
            "outline_width"     : "0.15",
            "outline_width_unit": "MM",
            "joinstyle"         : "bevel",
            "style"             : "solid",
        })
        ranges.append(QgsRendererRange(cat["lower"], cat["upper"], sym, cat["label"]))
    renderer = QgsGraduatedSymbolRenderer(field, ranges)
    layer.setRenderer(renderer)
    layer.triggerRepaint()

def apply_district_boundary_style(layer):
    sym = QgsFillSymbol.createSimple({
        "color"             : "0,0,0,0",
        "outline_color"     : "0,0,0,255",
        "outline_style"     : "solid",
        "outline_width"     : "0.3",
        "outline_width_unit": "MM",
    })
    layer.setRenderer(QgsSingleSymbolRenderer(sym))
    layer.triggerRepaint()

def add_district_labels(layer, field="Dist_Name", font_size=9.0, bold=True,
                         color=QColor(15, 23, 42, 255),
                         buf_color=QColor(255, 255, 255, 255)):
    lbl = QgsPalLayerSettings()
    
    if field == "Dist_Name":
        from imd_thunderstorm_warning_layout import DISTRICT_DISPLAY_NAMES
        case_expr_parts = []
        for orig, formatted in DISTRICT_DISPLAY_NAMES.items():
            escaped_orig = orig.replace("'", "''")
            escaped_fmt = formatted.replace("'", "''").replace("\n", "\\n")
            case_expr_parts.append(f"WHEN \"Dist_Name\" = '{escaped_orig}' THEN '{escaped_fmt}'")
        lbl.fieldName = "CASE " + " ".join(case_expr_parts) + " ELSE \"Dist_Name\" END"
        lbl.isExpression = True
    else:
        lbl.fieldName = field
        lbl.isExpression = False

    try:
        lbl.placement = QgsPalLayerSettings.AroundPoint
    except AttributeError:
        lbl.placement = QgsPalLayerSettings.OverPoint

    lbl.centroidInside = True
    lbl.fitInPolygonOnly = False
    lbl.drawLabels = True
    lbl.obstacle = True
    lbl.obstacleFactor = 0.7

    tf = QgsTextFormat()
    font_weight = QFont.Bold if bold else QFont.Normal
    tf.setFont(QFont("Arial", int(round(font_size)), font_weight))
    tf.setSize(float(font_size))
    tf.setSizeUnit(QgsUnitTypes.RenderPoints)
    tf.setColor(color)
    tf.setOpacity(1.0)

    size_expr = (
        "CASE "
        "  WHEN \"Dist_Name\" = 'Hyderabad' THEN 6.8 "
        "  WHEN \"Dist_Name\" IN ('Medchal Malkajgiri', 'Hanumakonda', 'Warangal', 'Rajanna Sircilla') THEN 7.5 "
        "  WHEN length(\"Dist_Name\") > 18 THEN 7.8 "
        "  WHEN length(\"Dist_Name\") > 12 THEN 8.4 "
        f"  ELSE {float(font_size)} "
        "END"
    )

    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(0.85)
    buf.setColor(buf_color)
    tf.setBuffer(buf)

    lbl.setFormat(tf)
    lbl.dataDefinedProperties().setProperty(
        QgsPalLayerSettings.Property.Size,
        QgsProperty.fromExpression(size_expr)
    )
    lbl.multilineAlign = QgsPalLayerSettings.MultiCenter
    layer.setLabeling(QgsVectorLayerSimpleLabeling(lbl))
    layer.setLabelsEnabled(True)
    layer.triggerRepaint()

def add_rainfall_intensity_district_labels(layer, field="Dist_Name"):
    from imd_thunderstorm_warning_layout import DISTRICT_DISPLAY_NAMES

    lbl = QgsPalLayerSettings()
    
    case_expr_parts = []
    for orig, formatted in DISTRICT_DISPLAY_NAMES.items():
        escaped_orig = orig.replace("'", "''")
        escaped_fmt = formatted.replace("'", "''").replace("\n", "\\n")
        case_expr_parts.append(f"WHEN \"Dist_Name\" = '{escaped_orig}' THEN '{escaped_fmt}'")
    lbl.fieldName = "CASE " + " ".join(case_expr_parts) + " ELSE \"Dist_Name\" END"
    lbl.isExpression = True

    lbl.placement = QgsPalLayerSettings.AroundPoint
    lbl.centroidInside = False
    lbl.fitInPolygonOnly = False
    lbl.drawLabels = True
    lbl.obstacle = False

    tf = QgsTextFormat()
    tf.setFont(QFont("Arial", 9, QFont.Bold))
    tf.setSize(9.0)
    tf.setSizeUnit(QgsUnitTypes.RenderPoints)
    tf.setColor(QColor("#002060"))

    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(1.20)
    buf.setColor(QColor(255, 255, 255, 255))
    tf.setBuffer(buf)
    lbl.setFormat(tf)

    x_cases = " ".join([f"WHEN \"Dist_Name\" = '{k}' THEN {v['lx']}" for k, v in RAINFALL_DISTRICT_CONFIG.items()])
    y_cases = " ".join([f"WHEN \"Dist_Name\" = '{k}' THEN {v['ly']}" for k, v in RAINFALL_DISTRICT_CONFIG.items()])
    
    x_expr = f"CASE {x_cases} ELSE $x END"
    y_expr = f"CASE {y_cases} ELSE $y END"

    size_expr = (
        "CASE "
        "  WHEN \"Dist_Name\" = 'Hyderabad' THEN 6.8 "
        "  WHEN \"Dist_Name\" = 'Medchal Malkajgiri' THEN 7.2 "
        "  WHEN \"Dist_Name\" IN ('Hanumakonda', 'Warangal', 'Rajanna Sircilla') THEN 7.5 "
        "  WHEN length(\"Dist_Name\") > 18 THEN 8.0 "
        "  WHEN length(\"Dist_Name\") > 12 THEN 8.5 "
        "  ELSE 9.0 "
        "END"
    )

    lbl.dataDefinedProperties().setProperty(
        QgsPalLayerSettings.Property.PositionX,
        QgsProperty.fromExpression(x_expr)
    )
    lbl.dataDefinedProperties().setProperty(
        QgsPalLayerSettings.Property.PositionY,
        QgsProperty.fromExpression(y_expr)
    )
    lbl.dataDefinedProperties().setProperty(
        QgsPalLayerSettings.Property.Hali,
        QgsProperty.fromValue('Center')
    )
    lbl.dataDefinedProperties().setProperty(
        QgsPalLayerSettings.Property.Vali,
        QgsProperty.fromValue('Half')
    )
    lbl.dataDefinedProperties().setProperty(
        QgsPalLayerSettings.Property.Size,
        QgsProperty.fromExpression(size_expr)
    )
    lbl.multilineAlign = QgsPalLayerSettings.MultiCenter

    layer.setLabeling(QgsVectorLayerSimpleLabeling(lbl))
    layer.setLabelsEnabled(True)
    layer.triggerRepaint()

def create_rainfall_cloud_symbols_layer(
    project: QgsProject,
    joined_layer: QgsVectorLayer,
    field_name: str = "inten1"
):
    sym_layer = QgsVectorLayer("Point?crs=EPSG:4326", f"RainfallSymbols_{field_name}", "memory")
    pr = sym_layer.dataProvider()
    pr.addAttributes([
        QgsField("dist_name", QVariant.String),
        QgsField("inten_val", QVariant.Int),
        QgsField("symbol_type", QVariant.String),
        QgsField("sym_size", QVariant.Double),
    ])
    sym_layer.updateFields()

    cloud_light_svg = os.path.join(config.TEMPLATE_PATH, "symbols", "cloud_light_rain.svg")
    cloud_mod_svg   = os.path.join(config.TEMPLATE_PATH, "symbols", "cloud_moderate_rain.svg")
    cloud_hvy_svg   = os.path.join(config.TEMPLATE_PATH, "symbols", "cloud_heavy_rain.svg")
    cloud_ext_svg   = os.path.join(config.TEMPLATE_PATH, "symbols", "cloud_extreme_rain.svg")

    features = []
    for feat in joined_layer.getFeatures():
        geom = feat.geometry()
        if not geom or geom.isEmpty():
            continue

        raw_val = feat[field_name]
        try:
            val = int(raw_val)
        except (ValueError, TypeError):
            val = 1

        dist_name = feat["Dist_Name"]
        if dist_name in RAINFALL_DISTRICT_CONFIG:
            cfg = RAINFALL_DISTRICT_CONFIG[dist_name]
            sym_x = cfg["sx"]
            sym_y = cfg["sy"]
            sym_size = cfg["size"]
        else:
            centroid = geom.centroid().asPoint()
            sym_x = centroid.x()
            sym_y = centroid.y() - 0.08
            sym_size = 7.2

        sym_pt = QgsGeometry.fromPointXY(QgsPointXY(sym_x, sym_y))
        if not geom.contains(sym_pt):
            try:
                res = geom.poleOfInaccessibility(0.002)
                poi_geom = res[0] if isinstance(res, (tuple, list)) else res
                poi_pt = poi_geom.asPoint()
                sym_x, sym_y = poi_pt.x(), poi_pt.y()
            except Exception:
                c = geom.centroid().asPoint()
                sym_x, sym_y = c.x(), c.y()

        if val >= 4:
            sym_type = "cloud_extreme"
        elif val == 3:
            sym_type = "cloud_heavy"
        elif val == 2:
            sym_type = "cloud_moderate"
        else:
            sym_type = "cloud_light"

        f = QgsFeature(sym_layer.fields())
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(sym_x, sym_y)))
        f["dist_name"] = dist_name
        f["inten_val"] = val
        f["symbol_type"] = sym_type
        f["sym_size"] = sym_size
        features.append(f)

    if features:
        pr.addFeatures(features)
        sym_layer.updateExtents()

        categories = []
        svg_map = [
            ("cloud_light", cloud_light_svg, "Light to moderate rain"),
            ("cloud_moderate", cloud_mod_svg, "Moderate to heavy rain"),
            ("cloud_heavy", cloud_hvy_svg, "Heavy to very heavy rain"),
            ("cloud_extreme", cloud_ext_svg, "Extremely heavy rain"),
        ]
        for cat_val, svg_path, cat_label in svg_map:
            svg_lyr = QgsSvgMarkerSymbolLayer(svg_path, 7.5)
            svg_lyr.setDataDefinedProperty(QgsSvgMarkerSymbolLayer.Property.Size, QgsProperty.fromField("sym_size"))
            sym = QgsMarkerSymbol()
            sym.changeSymbolLayer(0, svg_lyr)
            categories.append(QgsRendererCategory(cat_val, sym, cat_label))

        renderer = QgsCategorizedSymbolRenderer("symbol_type", categories)
        sym_layer.setRenderer(renderer)
        sym_layer.triggerRepaint()

    return sym_layer

def _apply_label_style(lbl: QgsLayoutItemLabel, text: str, font: QFont, color: QColor,
                       h_align=None, v_align=None):
    lbl.setText(text)
    tf = QgsTextFormat()
    tf.setFont(font)
    pt_size = font.pointSizeF() if font.pointSizeF() > 0 else (font.pointSize() if font.pointSize() > 0 else 8.0)
    tf.setSize(pt_size)
    tf.setSizeUnit(QgsUnitTypes.RenderPoints)
    tf.setColor(color)
    lbl.setTextFormat(tf)
    if h_align is not None:
        lbl.setHAlign(h_align)
    if v_align is not None:
        lbl.setVAlign(v_align)
    lbl.setFrameEnabled(False)
    lbl.setBackgroundEnabled(False)

def _build_manual_legend(layout, map_item, categories, legend_title, x, y, w, h):
    row_h = 8.0
    swatch_w = 8.0
    gap = 3.5
    text_w = w - swatch_w - gap

    effective_title = "Legend" if legend_title in ("Spatial Distribution", "warning", "spatial") else legend_title

    title_lbl = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(title_lbl)
    move_resize(title_lbl, x, y, w, 7.0)
    _apply_label_style(title_lbl, effective_title, QFont("Arial", 10, QFont.Bold), QColor("#000000"),
                       h_align=Qt.AlignLeft, v_align=Qt.AlignVCenter)

    cur_y = y + 8.5

    for cat in categories:
        hex_c = cat["color"].lstrip("#")
        try:
            r = int(hex_c[0:2], 16)
            g = int(hex_c[2:4], 16)
            b = int(hex_c[4:6], 16)
        except ValueError:
            r, g, b = 255, 255, 255

        swatch = QgsLayoutItemShape(layout)
        swatch.setShapeType(QgsLayoutItemShape.Rectangle)
        layout.addLayoutItem(swatch)
        move_resize(swatch, x, cur_y + 0.5, swatch_w, 5.5)
        swatch_sym = swatch.symbol()
        if swatch_sym:
            swatch_sym.setColor(QColor(r, g, b, 255))
            if swatch_sym.symbolLayerCount() > 0:
                swatch_sl = swatch_sym.symbolLayer(0)
                stroke_color = QColor("#333333")
                if hasattr(swatch_sl, "setStrokeColor"):
                    swatch_sl.setStrokeColor(stroke_color)
                elif hasattr(swatch_sl, "setOutlineColor"):
                    swatch_sl.setOutlineColor(stroke_color)
                if hasattr(swatch_sl, "setStrokeWidth"):
                    swatch_sl.setStrokeWidth(0.2)
                elif hasattr(swatch_sl, "setOutlineWidth"):
                    swatch_sl.setOutlineWidth(0.2)

        txt = QgsLayoutItemLabel(layout)
        layout.addLayoutItem(txt)
        move_resize(txt, x + swatch_w + gap, cur_y, text_w, 6.5)
        _apply_label_style(txt, cat["label"], QFont("Arial", 8, QFont.Normal), QColor("#1A202C"),
                           h_align=Qt.AlignLeft, v_align=Qt.AlignVCenter)

        cur_y += row_h

    return cur_y

def _build_qgis_legend(layout, map_item, legend_title, x, y, w, h):
    legend = QgsLayoutItemLegend(layout)
    layout.addLayoutItem(legend)
    move_resize(legend, x, y, w, h)

    legend.setTitle(legend_title)
    legend.setFrameEnabled(False)
    legend.setBackgroundEnabled(False)

    if _HAS_LEGEND_MODEL:
        try:
            custom_root = QgsLayerTree()
            display_layers = map_item.layers()
            for lyr in display_layers:
                if lyr and lyr.isValid():
                    custom_root.addLayer(lyr)
            if custom_root.children():
                legend_model = QgsLayerTreeModel(custom_root)
                legend_model.setFlag(QgsLayerTreeModel.ShowLegend, True)
                legend_model.setFlag(QgsLayerTreeModel.ShowLegendAsTree, False)
                legend_model.setFlag(QgsLayerTreeModel.AllowNodeReorder, False)
                legend_model.setFlag(QgsLayerTreeModel.AllowNodeRename, False)
                legend_model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility, False)
                legend.setModel(legend_model)
        except Exception as e:
            log(f"Legend layer tree setup warning: {e}", "WARN")

    legend.setLinkedMap(map_item)
    legend.setAutoUpdateModel(False)
    try:
        legend.updateLegend()
    except Exception:
        pass

    if QgsLegendStyle is not None:
        try:
            ts = legend.style(QgsLegendStyle.Title)
            ts.setFont(QFont("Arial", 9, QFont.Bold))
            legend.setStyle(QgsLegendStyle.Title, ts)

            gs = legend.style(QgsLegendStyle.Group)
            gs.setFont(QFont("Arial", 7))
            legend.setStyle(QgsLegendStyle.Group, gs)

            ls = legend.style(QgsLegendStyle.SymbolLabel)
            ls.setFont(QFont("Arial", 7))
            legend.setStyle(QgsLegendStyle.SymbolLabel, ls)
        except Exception as e:
            log(f"Legend style warning: {e}", "WARN")

    return legend

def _remove_existing_layout(project, name):
    for existing in project.layoutManager().layouts():
        if existing.name() == name:
            project.layoutManager().removeLayout(existing)

def build_layout(project, layout_name, display_layers,
                  title_text, subtitle_text="", legend_title="",
                  extent=None, estimated=False, show_scalebar=False,
                  legend_type="auto"):
    _remove_existing_layout(project, layout_name)

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(layout_name)

    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(PAGE_W, PAGE_H, MM))
    page.setBackgroundColor(QColor(255, 255, 255, 255))

    project.layoutManager().addLayout(layout)

    used_extent = extent or TELANGANA_EXTENT
    if estimated:
        title_text = "[ESTIMATED DATA] " + title_text

    if os.path.exists(PATHS["imd_logo"]):
        logo = QgsLayoutItemPicture(layout)
        layout.addLayoutItem(logo)
        move_resize(logo, LOGO_X, LOGO_Y, LOGO_W, LOGO_H)
        logo.setPicturePath(PATHS["imd_logo"])
        logo.setResizeMode(QgsLayoutItemPicture.Zoom)
        logo.setFrameEnabled(False)
        logo.setBackgroundEnabled(False)

    logo_lbl = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(logo_lbl)
    move_resize(logo_lbl, LOGO_LBL_X, LOGO_LBL_Y, LOGO_LBL_W, LOGO_LBL_H)
    _apply_label_style(logo_lbl, "Meteorological Centre\nHyderabad",
                       QFont("Arial", 8, QFont.Bold), QColor("#000000"),
                       h_align=Qt.AlignHCenter, v_align=Qt.AlignTop)

    title_lbl = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(title_lbl)
    move_resize(title_lbl, TITLE_X, TITLE_Y, TITLE_W, TITLE_H)
    title_txt = title_text if not subtitle_text else f"{title_text}\n{subtitle_text}"
    _apply_label_style(title_lbl, title_txt,
                       QFont("Arial", 13, QFont.Bold), QColor("#000000"),
                       h_align=Qt.AlignHCenter, v_align=Qt.AlignVCenter)

    if os.path.exists(NORTH_ARROW_SVG):
        north = QgsLayoutItemPicture(layout)
        layout.addLayoutItem(north)
        move_resize(north, NORTH_X, NORTH_Y, NORTH_W, NORTH_H)
        north.setPicturePath(NORTH_ARROW_SVG)
        north.setResizeMode(QgsLayoutItemPicture.Zoom)
        north.setFrameEnabled(False)
        north.setBackgroundEnabled(False)

        north_lbl = QgsLayoutItemLabel(layout)
        layout.addLayoutItem(north_lbl)
        move_resize(north_lbl, NORTH_LBL_X, NORTH_LBL_Y, NORTH_LBL_W, NORTH_LBL_H)
        _apply_label_style(north_lbl, "N",
                           QFont("Arial", 8, QFont.Bold), QColor("#000000"),
                           h_align=Qt.AlignHCenter, v_align=Qt.AlignTop)

    map_item = QgsLayoutItemMap(layout)
    map_item.setId("main_map")
    layout.addLayoutItem(map_item)
    move_resize(map_item, MAP_X, MAP_Y, MAP_W, MAP_H)
    map_item.attemptResize(QgsLayoutSize(MAP_W, MAP_H, MM))
    map_item.setLayers(display_layers)
    map_item.setKeepLayerSet(True)

    margin = 0.06
    dx = used_extent.width() * margin
    dy = used_extent.height() * margin
    buffered_extent = QgsRectangle(
        used_extent.xMinimum() - dx,
        used_extent.yMinimum() - dy,
        used_extent.xMaximum() + dx,
        used_extent.yMaximum() + dy,
    )
    map_item.setExtent(buffered_extent)
    map_item.zoomToExtent(buffered_extent)
    map_item.setFrameEnabled(False)
    map_item.setBackgroundEnabled(False)

    eff_title = legend_title or "Legend"
    if legend_type in ("warning", "rainfall", "spatial", "tmax", "tmin"):
        if legend_type == "warning":
            leg_cats = [{"label": c["label"], "color": c["color"]} for c in RAIN_WARNING_CATEGORIES]
        elif legend_type == "rainfall":
            leg_cats = RAINFALL_LEGEND_CATEGORIES
        elif legend_type == "spatial":
            leg_cats = [{"label": c["label"], "color": c["color"]} for c in SPATIAL_CATEGORIES]
        elif legend_type == "tmax":
            leg_cats = [{"label": c["label"], "color": c["color"]} for c in TMAX_CATEGORIES]
        else:
            leg_cats = [{"label": c["label"], "color": c["color"]} for c in TMIN_CATEGORIES]
        
        end_y = _build_manual_legend(layout, map_item, leg_cats, eff_title,
                                     LEGEND_X, LEGEND_Y, LEGEND_W, LEGEND_H)
        
        if legend_type == "warning":
            intensity_cats = [
                {"label": "Light to moderate rain",    "color": "#009900", "svg": "cloud_light_rain.svg",    "txt_color": "#000000"},
                {"label": "Moderate to heavy rain",    "color": "#FFFF00", "svg": "cloud_moderate_rain.svg", "txt_color": "#000000"},
                {"label": "Heavy to very heavy rain",  "color": "#FF9900", "svg": "cloud_heavy_rain.svg",    "txt_color": "#000000"},
                {"label": "Extremely heavy rain",      "color": "#FF0000", "svg": "cloud_extreme_rain.svg",  "txt_color": "#000000"},
            ]
            cur_y = end_y + 4.0
            strip_w = 62.0
            strip_h = 7.5
            icon_w  = 9.0
            icon_h  = 6.5

            for cat in intensity_cats:
                strip = QgsLayoutItemShape(layout)
                strip.setShapeType(QgsLayoutItemShape.Rectangle)
                layout.addLayoutItem(strip)
                move_resize(strip, LEGEND_X - 2.0, cur_y, strip_w, strip_h)
                strip_sym = strip.symbol()
                if strip_sym:
                    strip_sym.setColor(QColor(cat["color"]))
                    if strip_sym.symbolLayerCount() > 0:
                        sl = strip_sym.symbolLayer(0)
                        if hasattr(sl, "setStrokeColor"):
                            sl.setStrokeColor(QColor(cat["color"]))
                        elif hasattr(sl, "setOutlineColor"):
                            sl.setOutlineColor(QColor(cat["color"]))
                        if hasattr(sl, "setStrokeWidth"):
                            sl.setStrokeWidth(0.0)

                svg_path = os.path.join(config.TEMPLATE_PATH, "symbols", cat["svg"])
                if os.path.exists(svg_path):
                    ic = QgsLayoutItemPicture(layout)
                    layout.addLayoutItem(ic)
                    move_resize(ic, LEGEND_X - 2.0 + 1.2, cur_y + 0.5, icon_w, icon_h)
                    ic.setPicturePath(svg_path)
                    ic.setFrameEnabled(False)
                    ic.setBackgroundEnabled(False)

                txt_lbl = QgsLayoutItemLabel(layout)
                layout.addLayoutItem(txt_lbl)
                move_resize(txt_lbl, LEGEND_X - 2.0 + icon_w + 2.5, cur_y, strip_w - icon_w - 3.5, strip_h)
                _apply_label_style(txt_lbl, cat["label"],
                                   QFont("Arial", 8, QFont.Bold), QColor(cat["txt_color"]),
                                   h_align=Qt.AlignLeft, v_align=Qt.AlignVCenter)

                cur_y += strip_h + 2.0
    else:
        _build_qgis_legend(layout, map_item, eff_title,
                           LEGEND_X, LEGEND_Y, LEGEND_W, LEGEND_H)

    footer = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(footer)
    move_resize(footer, FOOTER_X, FOOTER_Y, FOOTER_W, FOOTER_H)
    _apply_label_style(footer, FOOTER_TEXT,
                       QFont("Arial", 5, QFont.Normal), QColor(50, 50, 50, 255),
                       h_align=Qt.AlignHCenter, v_align=Qt.AlignVCenter)
    footer.setMargin(0.5)

    try:
        map_item.refresh()
        layout.refresh()
        layout.updateBounds()
    except Exception as e:
        log(f"Layout refresh warning: {e}", "WARN")

    return layout

def export_layout(layout, out_base):
    exporter = QgsLayoutExporter(layout)
    files = []

    if EXPORT_PNG:
        path = out_base + ".png"
        delete_file_safe(path)
        s = QgsLayoutExporter.ImageExportSettings()
        s.dpi = PNG_DPI
        res = exporter.exportToImage(path, s)
        if res != QgsLayoutExporter.Success:
            raise Exception(f"[EXPORT FAIL] PNG export returned error code {res}: {os.path.basename(path)}")
        quality_check_output_strict(path)
        log(f"[OK] PNG exported: {os.path.basename(path)}")
        files.append(path)

    if EXPORT_PDF:
        path = out_base + ".pdf"
        delete_file_safe(path)
        s = QgsLayoutExporter.PdfExportSettings()
        res = exporter.exportToPdf(path, s)
        if res != QgsLayoutExporter.Success:
            raise Exception(f"[EXPORT FAIL] PDF export returned error code {res}: {os.path.basename(path)}")
        log(f"[OK] PDF exported: {os.path.basename(path)}")
        files.append(path)

    if not files:
        raise Exception(f"[EXPORT FAIL] No files produced for {os.path.basename(out_base)}")
    return files

def _generate_intensity_maps(project, intensity_gpkg, district_layer, today_str, estimated):
    log("[STEP] Generating rainfall intensity warning maps (5 days)", "STEP")
    inten_lyr = None
    for _ in range(5):
        inten_lyr = QgsVectorLayer(intensity_gpkg, "IntensityLayer", "ogr")
        if inten_lyr.isValid() and inten_lyr.featureCount() > 0:
            break
        time.sleep(0.4)

    if not inten_lyr or not inten_lyr.isValid():
        raise RuntimeError(f"Intensity GPKG invalid: {intensity_gpkg}")
    if inten_lyr.featureCount() == 0:
        raise RuntimeError(f"Intensity GPKG has 0 features: {intensity_gpkg}")

    project.addMapLayer(inten_lyr, False)
    files = []
    try:
        for day in WARNING_DAYS:
            log(f"[STEP] Intensity map Day {day}", "STEP")
            field = f"inten{day}"
            apply_graduated_fill(inten_lyr, field, RAIN_WARNING_CATEGORIES)
            add_rainfall_intensity_district_labels(inten_lyr)

            sym_layer = create_rainfall_cloud_symbols_layer(project, inten_lyr, field)
            if sym_layer:
                project.addMapLayer(sym_layer, False)

            display_layers = [sym_layer, inten_lyr, district_layer] if sym_layer else [inten_lyr, district_layer]

            layout = build_layout(
                project,
                layout_name   = f"IntensityMap_Day{day}",
                display_layers= display_layers,
                title_text    = f"Rainfall intensity warning based on {today_str} for Day{day}({day_date_str(day)})",
                subtitle_text = "",
                legend_title  = "Legend",
                estimated     = estimated,
                legend_type   = "warning",
            )
            out_base = os.path.join(PATHS["output_folder"], f"rainfall_intensity_day{day}")
            files += export_layout(layout, out_base)
            if sym_layer:
                project.removeMapLayer(sym_layer.id())
            log(f"[OK] Intensity Day {day} done")
    finally:
        project.removeMapLayer(inten_lyr.id())

    return files

def _generate_spatial_maps(project, spatial_gpkg, district_layer, today_str, estimated):
    log("[STEP] Generating spatial distribution maps (7 days)", "STEP")
    sp_lyr = None
    for _ in range(5):
        sp_lyr = QgsVectorLayer(spatial_gpkg, "SpatialLayer", "ogr")
        if sp_lyr.isValid() and sp_lyr.featureCount() > 0:
            break
        time.sleep(0.4)

    if not sp_lyr or not sp_lyr.isValid():
        raise RuntimeError(f"Spatial GPKG invalid: {spatial_gpkg}")
    if sp_lyr.featureCount() == 0:
        raise RuntimeError(f"Spatial GPKG has 0 features: {spatial_gpkg}")

    project.addMapLayer(sp_lyr, False)
    files = []
    try:
        for day in SPATIAL_DAYS:
            log(f"[STEP] Spatial map Day {day}", "STEP")
            field = f"spatial{day}"
            apply_graduated_fill(sp_lyr, field, SPATIAL_CATEGORIES)
            add_district_labels(sp_lyr)

            layout = build_layout(
                project,
                layout_name   = f"SpatialMap_Day{day}",
                display_layers= [sp_lyr, district_layer],
                title_text    = f"Rainfall forecast based on {today_str} for Day{day}({day_date_str(day)})",
                subtitle_text = "",
                legend_title  = "Spatial Distribution",
                estimated     = estimated,
                legend_type   = "spatial",
            )
            out_base = os.path.join(PATHS["output_folder"], f"rainfall_forecast_day{day}")
            files += export_layout(layout, out_base)
            log(f"[OK] Spatial Day {day} done")
    finally:
        project.removeMapLayer(sp_lyr.id())

    return files

def _generate_temp_maps(project, temp_gpkg, district_layer, today_str):
    log("[STEP] Generating temperature forecast maps (10 maps)", "STEP")
    temp_lyr = QgsVectorLayer(temp_gpkg, "TempLayer", "ogr")
    if not temp_lyr.isValid():
        raise RuntimeError(f"Temp GPKG invalid: {temp_gpkg}")
    if temp_lyr.featureCount() == 0:
        raise RuntimeError(f"Temp GPKG has 0 features: {temp_gpkg}")

    project.addMapLayer(temp_lyr, False)
    files = []
    try:
        for day in FORECAST_DAYS:
            for prefix, cats, title_word, leg_title, leg_type in [
                ("tmax", TMAX_CATEGORIES, "Maximum Temperature", "Max Temp (°C)", "tmax"),
                ("tmin", TMIN_CATEGORIES, "Minimum Temperature", "Min Temp (°C)", "tmin"),
            ]:
                log(f"[STEP] Temp map {prefix.upper()} Day {day}", "STEP")
                field = f"{prefix}{day}"
                apply_graduated_fill(temp_lyr, field, cats)
                add_district_labels(temp_lyr)

                layout = build_layout(
                    project,
                    layout_name   = f"TempMap_{prefix}_Day{day}",
                    display_layers= [temp_lyr, district_layer],
                    title_text    = f"{title_word} Forecast — Day {day}  ({day_date_str(day)})",
                    legend_title  = leg_title,
                    legend_type   = leg_type,
                )
                out_base = os.path.join(PATHS["output_folder"], f"{prefix}_day{day}_{today_str}")
                files += export_layout(layout, out_base)
                log(f"[OK] Temp {prefix.upper()} Day {day} done")
    finally:
        project.removeMapLayer(temp_lyr.id())

    return files

def main(target_module: str = None, input_file: str = None):
    if target_module is None:
        target_module = "all"
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--module" and i < len(sys.argv) - 1:
                target_module = sys.argv[i + 1].lower()
            elif arg.startswith("--module="):
                target_module = arg.split("=", 1)[1].lower()

    if input_file is None:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--input" and i < len(sys.argv) - 1:
                input_file = sys.argv[i + 1]
            elif arg.startswith("--input="):
                input_file = arg.split("=", 1)[1]

    if target_module not in ("rain", "summer", "all"):
        target_module = "all"

    start = datetime.datetime.now()
    today_str = start.strftime("%d-%m-%Y")
    is_estimated = False
    all_files = []

    log(f"Run date : {today_str}")
    log(f"Run time : {start.strftime('%H:%M:%S')}")
    log(f"Module   : {target_module.upper()}")

    write_run_log("RUNNING", 0, [], start, progress=5, step=f"Initializing {target_module.upper()} Pipeline", module=target_module)

    from utils.excel_parser import (
        parse_multi_hazard_excel_memory,
        parse_summer_excel_memory,
        parse_any_excel_memory,
    )

    excel_target = input_file
    if not excel_target or not os.path.exists(excel_target):
        search_dirs = [config.CSV_PATH, os.path.join(config.PROJECT_ROOT, "data")]
        found_files = []
        for sdir in search_dirs:
            if os.path.isdir(sdir):
                for f in os.listdir(sdir):
                    if f.lower().endswith(".xlsx") and not f.startswith("~$"):
                        fpath = os.path.join(sdir, f)
                        found_files.append((os.path.getmtime(fpath), fpath))

        if found_files:
            found_files.sort(reverse=True)
            if target_module == "summer":
                summer_files = [fp for _, fp in found_files if "summer" in os.path.basename(fp).lower()]
                excel_target = summer_files[0] if summer_files else found_files[0][1]
            else:
                rain_files = [fp for _, fp in found_files if "multi_hazard" in os.path.basename(fp).lower() or "rain" in os.path.basename(fp).lower()]
                excel_target = rain_files[0] if rain_files else found_files[0][1]

    if not excel_target or not os.path.exists(excel_target):
        msg = "CRITICAL: No input Excel workbook (.xlsx) found in data directory"
        log(msg, "ERROR")
        write_run_log("FAILED", 0, [msg], start, progress=0, step="Input Excel Missing", module=target_module)
        send_alert("Excel Missing", msg)
        raise RuntimeError(msg)

    log(f"[OK] Ingesting Excel Workbook: {os.path.basename(excel_target)}")

    rain_parsed = None
    summer_parsed = None
    if target_module in ("rain", "all"):
        if "summer" not in os.path.basename(excel_target).lower():
            rain_parsed = parse_multi_hazard_excel_memory(excel_target)
            log(f"[OK] Parsed 7-Day Multi-Hazard Forecast: {len(rain_parsed['districts'])} districts")
        else:
            rain_parsed = parse_any_excel_memory(excel_target)

    if target_module in ("summer", "all"):
        summer_file = excel_target if "summer" in os.path.basename(excel_target).lower() else os.path.join(config.CSV_PATH, "SUMMER.xlsx")
        if os.path.exists(summer_file):
            summer_parsed = parse_summer_excel_memory(summer_file)
            log(f"[OK] Parsed Summer Temperature Forecast: {len(summer_parsed['districts'])} districts")
        elif target_module == "summer":
            msg = f"CRITICAL: Summer Excel file missing: {summer_file}"
            log(msg, "ERROR")
            write_run_log("FAILED", 0, [msg], start, progress=0, step="Summer Excel Missing", module=target_module)
            raise RuntimeError(msg)

    if not os.path.exists(PATHS["district_shp"]):
        msg = f"CRITICAL: District shapefile missing: {PATHS['district_shp']}"
        log(msg, "ERROR")
        write_run_log("FAILED", 0, [msg], start, progress=0, step="Shapefile Missing", module=target_module)
        send_alert("Shapefile Missing", msg)
        raise RuntimeError(msg)

    log("[OK] District shapefile found")

    ensure_dir(PATHS["output_folder"])
    ensure_dir(PATHS["log_folder"])

    project = QgsProject.instance()
    remove_all_layers(project)

    district_layer = QgsVectorLayer(PATHS["district_shp"], "DistrictBoundary", "ogr")
    if not district_layer.isValid():
        msg = f"District shapefile failed to load: {PATHS['district_shp']}"
        log(msg, "ERROR")
        write_run_log("FAILED", 0, [msg], start, progress=0, step="Shapefile Load Error", module=target_module)
        send_alert("QGIS Load Error", msg)
        raise RuntimeError(msg)

    project.addMapLayer(district_layer, False)
    apply_district_boundary_style(district_layer)
    district_layer.setLabelsEnabled(False)
    log(f"[OK] Districts loaded: {district_layer.featureCount()} features")

    write_run_log("RUNNING", 0, [], start, progress=50, step="Joining In-Memory Attributes to Vector Layer", module=target_module)

    spatial_gpkg = None
    warning_gpkg = None
    intensity_gpkg = None
    temp_gpkg = None

    if rain_parsed and rain_parsed.get("districts"):
        log("[STEP] Joining in-memory 7-day spatial forecast attributes", "STEP")
        spatial_fields = [f"spatial{d}" for d in SPATIAL_DAYS]
        spatial_gpkg_target = os.path.join(PATHS["output_folder"], "SpatialJoined.gpkg")
        spatial_gpkg = join_memory_data_to_shapefile(
            district_layer, rain_parsed["districts"], SHP_NAME_FIELD, spatial_fields, spatial_gpkg_target
        )

        log("[STEP] Joining in-memory 5-day thunderstorm warning attributes", "STEP")
        warning_fields = [f"warning{d}" for d in WARNING_DAYS] + [f"tslg{d}" for d in WARNING_DAYS]
        warning_gpkg_target = os.path.join(PATHS["output_folder"], "WarningJoined.gpkg")
        warning_gpkg = join_memory_data_to_shapefile(
            district_layer, rain_parsed["districts"], SHP_NAME_FIELD, warning_fields, warning_gpkg_target
        )

        if rain_parsed.get("has_intensity_data", False):
            log("[STEP] Joining in-memory 5-day rainfall intensity attributes", "STEP")
            intensity_fields = [f"inten{d}" for d in WARNING_DAYS]
            intensity_gpkg_target = os.path.join(PATHS["output_folder"], "IntensityJoined.gpkg")
            intensity_gpkg = join_memory_data_to_shapefile(
                district_layer, rain_parsed["districts"], SHP_NAME_FIELD, intensity_fields, intensity_gpkg_target
            )
        else:
            log("[INFO] No heavy rainfall intensity tokens (HR/VHR/EHR) present — intensity maps skipped.")

    if summer_parsed and summer_parsed.get("districts"):
        log("[STEP] Joining in-memory summer temperature attributes", "STEP")
        temp_fields = [f"tmax{d}" for d in FORECAST_DAYS] + [f"tmin{d}" for d in FORECAST_DAYS]
        temp_gpkg_target = os.path.join(PATHS["output_folder"], "TempJoined.gpkg")
        temp_gpkg = join_memory_data_to_shapefile(
            district_layer, summer_parsed["districts"], SHP_NAME_FIELD, temp_fields, temp_gpkg_target
        )

    if spatial_gpkg:
        log("[STEP] Generating 7-Day Spatial Distribution Maps", "STEP")
        write_run_log("RUNNING", len(all_files), [], start, progress=55, step="Generating 7-Day Spatial Rainfall Maps", module=target_module)
        try:
            sp_files = _generate_spatial_maps(project, spatial_gpkg, district_layer, today_str, is_estimated)
            all_files += sp_files
            log(f"[OK] Spatial maps: {len(sp_files)} file(s)")
        except Exception as e:
            msg = f"Spatial map generation failed: {e}\n{traceback.format_exc()}"
            log(msg, "ERROR")
            write_run_log("FAILED", 0, [str(e)], start, progress=0, step="Spatial Map Failed", module=target_module)
            raise RuntimeError(f"Spatial map failure aborts pipeline: {e}") from e

    if warning_gpkg:
        log("[STEP] Generating 5-Day Thunderstorm & Wind Warning Maps", "STEP")
        write_run_log("RUNNING", len(all_files), [], start, progress=65, step="Generating Thunderstorm & Wind Warning Maps", module=target_module)
        try:
            try:
                from scripts.imd_thunderstorm_warning_layout import generate_thunderstorm_warning_maps
            except ImportError:
                from imd_thunderstorm_warning_layout import generate_thunderstorm_warning_maps
            ts_files = generate_thunderstorm_warning_maps(project, warning_gpkg, PATHS["output_folder"], today_str)
            all_files += ts_files
            log(f"[OK] Thunderstorm Warning maps: {len(ts_files)} file(s)")
        except Exception as e:
            log(f"Thunderstorm warning map generation warning: {e}\n{traceback.format_exc()}", "WARN")

    if intensity_gpkg:
        log("[STEP] Generating 5-Day Rainfall Intensity Warning Maps", "STEP")
        write_run_log("RUNNING", len(all_files), [], start, progress=75, step="Generating Rainfall Intensity Warning Maps", module=target_module)
        try:
            in_files = _generate_intensity_maps(project, intensity_gpkg, district_layer, today_str, is_estimated)
            all_files += in_files
            log(f"[OK] Rainfall Intensity maps: {len(in_files)} file(s)")
        except Exception as e:
            msg = f"Intensity map generation failed: {e}\n{traceback.format_exc()}"
            log(msg, "ERROR")
            write_run_log("FAILED", 0, [str(e)], start, progress=0, step="Intensity Map Failed", module=target_module)
            raise RuntimeError(f"Intensity map failure aborts pipeline: {e}") from e

    if temp_gpkg:
        log("[STEP] Generating Temperature Forecast Maps", "STEP")
        write_run_log("RUNNING", len(all_files), [], start, progress=82, step="Generating Max & Min Temperature Forecast Maps", module=target_module)
        try:
            tm_files = _generate_temp_maps(project, temp_gpkg, district_layer, today_str)
            all_files += tm_files
            log(f"[OK] Temperature maps: {len(tm_files)} file(s)")
        except Exception as e:
            msg = f"Temperature map generation failed: {e}\n{traceback.format_exc()}"
            log(msg, "ERROR")
            write_run_log("FAILED", 0, [str(e)], start, progress=0, step="Temp Map Failed", module=target_module)
            raise RuntimeError(f"Temperature map failure aborts pipeline: {e}") from e

        log("[STEP] Generating 5-Day Temperature Grid Summary Maps", "STEP")
        write_run_log("RUNNING", len(all_files), [], start, progress=90, step="Generating 5-Day Temperature Grid Summary Maps", module=target_module)
        try:
            try:
                from scripts.imd_5day_temp_grid_layout import generate_5day_temp_grid_map
            except ImportError:
                from imd_5day_temp_grid_layout import generate_5day_temp_grid_map
            grid_max_files = generate_5day_temp_grid_map(project, temp_gpkg, PATHS["output_folder"], "Maximum", today_str)
            grid_min_files = generate_5day_temp_grid_map(project, temp_gpkg, PATHS["output_folder"], "Minimum", today_str)
            all_files += grid_max_files + grid_min_files
            log(f"[OK] 5-Day Temperature Grid maps: {len(grid_max_files) + len(grid_min_files)} file(s)")
        except Exception as e:
            log(f"5-Day Temp Grid map generation warning: {e}\n{traceback.format_exc()}", "WARN")

    log("[STEP] Running final quality checks on all outputs", "STEP")
    write_run_log("RUNNING", len(all_files), [], start, progress=97, step="Executing Quality Control Checks", module=target_module)

    qc_failures = []
    for fpath in all_files:
        if fpath.endswith(".png"):
            try:
                quality_check_output_strict(fpath)
            except Exception as e:
                qc_failures.append(str(e))

    if qc_failures:
        msg = f"QC failed for {len(qc_failures)} output(s): {qc_failures[0]}"
        log(msg, "ERROR")
        write_run_log("FAILED", 0, qc_failures, start, progress=0, step="QC Failed", module=target_module)
        write_system_health("QC FAILED", msg)
        send_alert("QC Failed", msg)
        raise RuntimeError(msg)

    log(f"[OK] All {len([f for f in all_files if f.endswith('.png')])} PNG outputs passed QC")

    elapsed = (datetime.datetime.now() - start).seconds
    png_count = len([f for f in all_files if f.endswith(".png")])

    write_run_log("SUCCESS", png_count, [], start, datetime.datetime.now(), is_estimated, progress=100, step="Completed Successfully", module=target_module)

    log(f"VECTOR AUTOMATION [{target_module.upper()}] SUCCESS: {len(all_files)} files in {elapsed}s")

def _qgis_shutdown() -> None:
    try:
        QgsProject.instance().clear()
    except Exception:
        pass
    if _qgs_app is not None and _QGIS_INITIALIZED:
        try:
            _qgs_app.exitQgis()
        except Exception:
            pass

if __name__ == "__main__":
    _exit_code = 0
    try:
        main()
    except Exception as _fatal:
        print(f"[CRITICAL ERROR] Pipeline aborted: {_fatal}")
        traceback.print_exc()
        try:
            write_system_health("FAILED", f"Vector pipeline aborted: {_fatal}")
        except Exception:
            pass
        _exit_code = 1
    finally:
        _qgis_shutdown()
    sys.exit(_exit_code)