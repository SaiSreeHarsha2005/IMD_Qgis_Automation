import os
import sys
import datetime
import warnings
from typing import List, Dict, Tuple, Optional

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from osgeo import gdal
    gdal.PushErrorHandler('CPLQuietErrorHandler')
except ImportError:
    pass

from qgis.core import (
    Qgis,
    QgsProject,
    QgsVectorLayer,
    QgsGraduatedSymbolRenderer,
    QgsRendererRange,
    QgsFillSymbol,
    QgsMarkerSymbol,
    QgsSvgMarkerSymbolLayer,
    QgsRasterMarkerSymbolLayer,
    QgsSingleSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsPrintLayout,
    QgsLayoutItemMap,
    QgsLayoutItemLabel,
    QgsLayoutItemPicture,
    QgsLayoutItemShape,
    QgsLayoutSize,
    QgsLayoutPoint,
    QgsUnitTypes,
    QgsLayoutExporter,
    QgsRectangle,
    QgsGeometry,
    QgsPointXY,
    QgsFeature,
    QgsField,
    QgsProperty,
)
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QColor, QFont

import config

WARNING_COLOR_RAMP = [
    (0.5, 1.5, "#009900", "No Warning (No action)"),
    (1.5, 2.5, "#FFFF00", "Watch (Be updated)"),
    (2.5, 3.5, "#FF9900", "Alert (Be prepared)"),
    (3.5, 4.5, "#FF0000", "Warning (Take action)"),
]

DISTRICT_DISPLAY_NAMES = {
    "Adilabad": "Adilabad",
    "Bhadradri Kothagudem": "Bhadradri\nKothagudem",
    "Hanumakonda": "Hanumakonda",
    "Hyderabad": "Hyderabad",
    "Jagtial": "Jagtial",
    "Jangoan": "Jangaon",
    "Jayashankar Bhupalpally": "Jayashankar\nBhupalpally",
    "Jogulamba Gadwal": "Jogulamba\nGadwal",
    "Kamareddy": "Kamareddy",
    "Karimnagar": "Karimnagar",
    "Khammam": "Khammam",
    "Kumurambheem Asifabad": "Kumurambheem\nAsifabad",
    "Mahabubabad": "Mahabubabad",
    "Mahabubnagar": "Mahabubnagar",
    "Mancherial": "Mancherial",
    "Medak": "Medak",
    "Medchal Malkajgiri": "Medchal\nMalkajgiri",
    "Mulugu": "Mulugu",
    "Nagarkurnool": "Nagarkurnool",
    "Nalgonda": "Nalgonda",
    "Narayanpet": "Narayanpet",
    "Nirmal": "Nirmal",
    "Nizamabad": "Nizamabad",
    "Peddapalli": "Peddapalli",
    "Rajanna Sircilla": "Rajanna\nSircilla",
    "Rangareddy": "Rangareddy",
    "Sangareddy": "Sangareddy",
    "Siddipet": "Siddipet",
    "Suryapet": "Suryapet",
    "Vikarabad": "Vikarabad",
    "Wanaparthy": "Wanaparthy",
    "Warangal": "Warangal",
    "Yadadri Bhuvanagiri": "Yadadri\nBhuvanagiri",
}

DISTRICT_ANCHORS: Dict[str, Dict[str, float]] = {
    "Adilabad":                {"sx": 78.565, "sy": 19.560, "size": 5.8},
    "Bhadradri Kothagudem":    {"sx": 80.680, "sy": 17.760, "size": 6.2},
    "Hanumakonda":             {"sx": 79.460, "sy": 18.065, "size": 4.6},
    "Hyderabad":               {"sx": 78.467, "sy": 17.435, "size": 3.8},
    "Jagtial":                 {"sx": 78.876, "sy": 18.880, "size": 5.6},
    "Jangoan":                 {"sx": 79.276, "sy": 17.795, "size": 5.4},
    "Jayashankar Bhupalpally": {"sx": 79.928, "sy": 18.555, "size": 5.8},
    "Jogulamba Gadwal":        {"sx": 77.781, "sy": 16.180, "size": 5.4},
    "Kamareddy":               {"sx": 78.063, "sy": 18.375, "size": 5.6},
    "Karimnagar":              {"sx": 79.238, "sy": 18.425, "size": 5.4},
    "Khammam":                 {"sx": 80.356, "sy": 17.255, "size": 5.8},
    "Kumurambheem Asifabad":   {"sx": 79.400, "sy": 19.410, "size": 5.8},
    "Mahabubabad":             {"sx": 79.987, "sy": 17.720, "size": 5.6},
    "Mahabubnagar":            {"sx": 77.990, "sy": 16.820, "size": 5.6},
    "Mancherial":              {"sx": 79.517, "sy": 19.045, "size": 5.8},
    "Medak":                   {"sx": 78.258, "sy": 18.005, "size": 5.4},
    "Medchal Malkajgiri":      {"sx": 78.558, "sy": 17.605, "size": 4.4},
    "Mulugu":                  {"sx": 80.338, "sy": 18.345, "size": 5.8},
    "Nagarkurnool":            {"sx": 78.589, "sy": 16.480, "size": 6.0},
    "Nalgonda":                {"sx": 79.193, "sy": 16.935, "size": 6.0},
    "Narayanpet":              {"sx": 77.581, "sy": 16.720, "size": 5.2},
    "Nirmal":                  {"sx": 78.317, "sy": 19.165, "size": 5.6},
    "Nizamabad":               {"sx": 78.205, "sy": 18.755, "size": 5.6},
    "Peddapalli":              {"sx": 79.455, "sy": 18.670, "size": 5.4},
    "Rajanna Sircilla":        {"sx": 78.760, "sy": 18.475, "size": 5.0},
    "Rangareddy":              {"sx": 78.412, "sy": 17.185, "size": 5.8},
    "Sangareddy":              {"sx": 77.874, "sy": 17.840, "size": 5.6},
    "Siddipet":                {"sx": 78.848, "sy": 18.065, "size": 5.6},
    "Suryapet":                {"sx": 79.755, "sy": 17.135, "size": 5.6},
    "Vikarabad":               {"sx": 77.746, "sy": 17.305, "size": 5.6},
    "Wanaparthy":              {"sx": 78.037, "sy": 16.380, "size": 5.4},
    "Warangal":                {"sx": 79.750, "sy": 17.965, "size": 4.8},
    "Yadadri Bhuvanagiri":     {"sx": 78.995, "sy": 17.510, "size": 5.6},
}

def style_shape(shape: QgsLayoutItemShape, fill_hex: str, stroke_hex: str, stroke_width: float = 0.3) -> None:
    sym = shape.symbol()
    if sym:
        sym.setColor(QColor(fill_hex))
        if sym.symbolLayerCount() > 0:
            sl = sym.symbolLayer(0)
            if hasattr(sl, "setStrokeColor"):
                sl.setStrokeColor(QColor(stroke_hex))
            elif hasattr(sl, "setOutlineColor"):
                sl.setOutlineColor(QColor(stroke_hex))
            if hasattr(sl, "setStrokeWidth"):
                sl.setStrokeWidth(stroke_width)
            elif hasattr(sl, "setOutlineWidth"):
                sl.setOutlineWidth(stroke_width)

def apply_label_style(lbl: QgsLayoutItemLabel, text: str, font: QFont, color: QColor,
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

def apply_warning_style(layer: QgsVectorLayer, field_name: str = "warning1") -> None:
    ranges = []
    for min_val, max_val, hex_color, label in WARNING_COLOR_RAMP:
        symbol = QgsFillSymbol.createSimple({
            "color": hex_color,
            "outline_color": "#1A1A1A",
            "outline_width": "0.35",
        })
        ranges.append(QgsRendererRange(min_val, max_val, symbol, label))

    renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
    layer.setRenderer(renderer)

    pal = QgsPalLayerSettings()
    
    case_expr_parts = []
    for orig, formatted in DISTRICT_DISPLAY_NAMES.items():
        escaped_orig = orig.replace("'", "''")
        escaped_fmt = formatted.replace("'", "''").replace("\n", "\\n")
        case_expr_parts.append(f"WHEN \"Dist_Name\" = '{escaped_orig}' THEN '{escaped_fmt}'")
    
    label_expr = "CASE " + " ".join(case_expr_parts) + " ELSE \"Dist_Name\" END"
    pal.fieldName = label_expr
    pal.isExpression = True

    pal.placement = QgsPalLayerSettings.AroundPoint
    pal.centroidInside = True
    pal.fitInPolygonOnly = False

    tf = QgsTextFormat()
    tf.setFont(QFont("Arial", 8, QFont.Bold))
    tf.setColor(QColor("#0F172A"))

    size_expr = (
        "CASE "
        "  WHEN \"Dist_Name\" = 'Hyderabad' THEN 6.5 "
        "  WHEN \"Dist_Name\" IN ('Medchal Malkajgiri', 'Hanumakonda', 'Warangal', 'Rajanna Sircilla') THEN 7.2 "
        "  WHEN length(\"Dist_Name\") > 18 THEN 7.5 "
        "  WHEN length(\"Dist_Name\") > 12 THEN 8.0 "
        "  ELSE 8.8 "
        "END"
    )

    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(0.80)
    buf.setColor(QColor("#FFFFFF"))
    buf.setOpacity(1.0)
    tf.setBuffer(buf)

    pal.setFormat(tf)
    pal.dataDefinedProperties().setProperty(
        QgsPalLayerSettings.Property.Size,
        QgsProperty.fromExpression(size_expr)
    )
    pal.multilineAlign = QgsPalLayerSettings.MultiCenter
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)
    layer.triggerRepaint()

def create_weather_symbols_layer(
    project: QgsProject,
    joined_layer: QgsVectorLayer,
    field_name: str = "warning1"
) -> Optional[QgsVectorLayer]:
    sym_layer = QgsVectorLayer("Point?crs=EPSG:4326", f"Symbols_{field_name}", "memory")
    pr = sym_layer.dataProvider()
    pr.addAttributes([
        QgsField("dist_name", QVariant.String),
        QgsField("warning_val", QVariant.Int),
        QgsField("symbol_type", QVariant.String),
        QgsField("sym_size", QVariant.Double),
    ])
    sym_layer.updateFields()

    wind_png = os.path.join(config.TEMPLATE_PATH, "symbols", "Wind_warning.png")
    windsock_svg = os.path.join(config.TEMPLATE_PATH, "symbols", "windsock.svg")
    wind_symbol_path = wind_png if os.path.exists(wind_png) else windsock_svg

    cloud_png = os.path.join(config.TEMPLATE_PATH, "symbols", "cloud.png")
    ts_wind_svg = os.path.join(config.TEMPLATE_PATH, "symbols", "thunderstorm_wind.svg")
    ts_symbol_path = cloud_png if os.path.exists(cloud_png) else ts_wind_svg

    ts_svg = os.path.join(config.TEMPLATE_PATH, "symbols", "thunderstorm.svg")

    features = []
    for feat in joined_layer.getFeatures():
        geom = feat.geometry()
        if not geom or geom.isEmpty():
            continue

        warn_val = feat[field_name]
        try:
            warn_num = int(warn_val)
        except (ValueError, TypeError):
            continue

        dist_name = feat["Dist_Name"]
        if dist_name in DISTRICT_ANCHORS:
            anchor = DISTRICT_ANCHORS[dist_name]
            sym_x = anchor["sx"]
            sym_y = anchor["sy"]
            base_size = anchor["size"]
        else:
            centroid = geom.centroid().asPoint()
            sym_x = centroid.x()
            sym_y = centroid.y() + 0.05
            base_size = 5.6

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

        if warn_num >= 2:
            sym_type = "thunderstorm_wind"
            sym_size = base_size * 1.15
        else:
            sym_type = "windsock"
            sym_size = base_size * 0.95

        f = QgsFeature(sym_layer.fields())
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(sym_x, sym_y)))
        f["dist_name"] = dist_name
        f["warning_val"] = warn_num
        f["symbol_type"] = sym_type
        f["sym_size"] = sym_size
        features.append(f)

    if features:
        pr.addFeatures(features)
        sym_layer.updateExtents()

        categories = []

        if wind_symbol_path.lower().endswith(".svg"):
            ws_layer = QgsSvgMarkerSymbolLayer(wind_symbol_path, 5.2)
            ws_layer.setDataDefinedProperty(QgsSvgMarkerSymbolLayer.Property.Size, QgsProperty.fromField("sym_size"))
        else:
            ws_layer = QgsRasterMarkerSymbolLayer(wind_symbol_path)
            ws_layer.setSize(5.2)
            ws_layer.setDataDefinedProperty(QgsRasterMarkerSymbolLayer.Property.Size, QgsProperty.fromField("sym_size"))
        ws_sym = QgsMarkerSymbol()
        ws_sym.changeSymbolLayer(0, ws_layer)
        categories.append(QgsRendererCategory("windsock", ws_sym, "Wind Warning"))

        if ts_symbol_path.lower().endswith(".svg"):
            tsw_layer = QgsSvgMarkerSymbolLayer(ts_symbol_path, 6.2)
            tsw_layer.setDataDefinedProperty(QgsSvgMarkerSymbolLayer.Property.Size, QgsProperty.fromField("sym_size"))
        else:
            tsw_layer = QgsRasterMarkerSymbolLayer(ts_symbol_path)
            tsw_layer.setSize(6.2)
            tsw_layer.setDataDefinedProperty(QgsRasterMarkerSymbolLayer.Property.Size, QgsProperty.fromField("sym_size"))
        tsw_sym = QgsMarkerSymbol()
        tsw_sym.changeSymbolLayer(0, tsw_layer)
        categories.append(QgsRendererCategory("thunderstorm_wind", tsw_sym, "Thunderstorm with Wind"))

        ts_layer = QgsSvgMarkerSymbolLayer(ts_svg, 5.8)
        ts_layer.setDataDefinedProperty(QgsSvgMarkerSymbolLayer.Property.Size, QgsProperty.fromField("sym_size"))
        ts_sym = QgsMarkerSymbol()
        ts_sym.changeSymbolLayer(0, ts_layer)
        categories.append(QgsRendererCategory("thunderstorm", ts_sym, "Thunderstorm"))

        sym_renderer = QgsCategorizedSymbolRenderer("symbol_type", categories)
        sym_layer.setRenderer(sym_renderer)
        sym_layer.triggerRepaint()
        project.addMapLayer(sym_layer)
        return sym_layer

    return None

def build_thunderstorm_layout(
    project: QgsProject,
    joined_layer: QgsVectorLayer,
    day_num: int = 1,
    date_str: str = "",
    symbol_layer: Optional[QgsVectorLayer] = None
) -> QgsPrintLayout:
    layout_name = f"Thunderstorm_Warning_Day{day_num}"
    
    mgr = project.layoutManager()
    for existing in mgr.printLayouts():
        if existing.name() == layout_name:
            mgr.removeLayout(existing)
            break

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(layout_name)
    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(297, 210, QgsUnitTypes.LayoutMillimeters))
    page.setBackgroundColor(QColor(255, 255, 255, 255))
    mgr.addLayout(layout)

    extent = QgsRectangle(76.80, 15.55, 81.75, 20.10)

    imd_logo = os.path.join(config.TEMPLATE_PATH, "IMD_LOGO.png")
    if os.path.exists(imd_logo):
        logo = QgsLayoutItemPicture(layout)
        logo.setPicturePath(imd_logo)
        logo.attemptMove(QgsLayoutPoint(12, 3.5, QgsUnitTypes.LayoutMillimeters))
        logo.attemptResize(QgsLayoutSize(21, 21, QgsUnitTypes.LayoutMillimeters))
        logo.setResizeMode(logo.Zoom)
        logo.setFrameEnabled(False)
        logo.setBackgroundEnabled(False)
        layout.addLayoutItem(logo)

        logo_lbl = QgsLayoutItemLabel(layout)
        apply_label_style(logo_lbl, "Meteorological Centre\nHyderabad",
                          QFont("Arial", 8, QFont.Bold), QColor("#000000"),
                          h_align=Qt.AlignHCenter)
        logo_lbl.attemptMove(QgsLayoutPoint(2, 25.0, QgsUnitTypes.LayoutMillimeters))
        logo_lbl.attemptResize(QgsLayoutSize(42, 9, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(logo_lbl)

    t1 = QgsLayoutItemLabel(layout)
    apply_label_style(t1, "Meteorological Centre Hyderabad",
                      QFont("Arial", 16, QFont.Bold), QColor("#000000"),
                      h_align=Qt.AlignCenter)
    t1.attemptMove(QgsLayoutPoint(46, 3.5, QgsUnitTypes.LayoutMillimeters))
    t1.attemptResize(QgsLayoutSize(206, 8.5, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(t1)

    today_formatted = date_str or datetime.date.today().strftime("%d-%m-%Y")
    sub_txt = f"Thunderstorm warning based on {today_formatted} for Day {day_num} ({today_formatted})"
    t2 = QgsLayoutItemLabel(layout)
    apply_label_style(t2, sub_txt,
                      QFont("Arial", 11, QFont.Bold), QColor("#000000"),
                      h_align=Qt.AlignCenter)
    t2.attemptMove(QgsLayoutPoint(46, 12.5, QgsUnitTypes.LayoutMillimeters))
    t2.attemptResize(QgsLayoutSize(206, 6.5, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(t2)

    if os.path.exists(config.NORTH_ARROW_SVG):
        north = QgsLayoutItemPicture(layout)
        north.setPicturePath(config.NORTH_ARROW_SVG)
        north.attemptMove(QgsLayoutPoint(268, 3.5, QgsUnitTypes.LayoutMillimeters))
        north.attemptResize(QgsLayoutSize(15, 17, QgsUnitTypes.LayoutMillimeters))
        north.setResizeMode(north.Zoom)
        north.setFrameEnabled(False)
        north.setBackgroundEnabled(False)
        layout.addLayoutItem(north)

        north_lbl = QgsLayoutItemLabel(layout)
        apply_label_style(north_lbl, "N",
                          QFont("Arial", 8, QFont.Bold), QColor("#000000"),
                          h_align=Qt.AlignHCenter)
        north_lbl.attemptMove(QgsLayoutPoint(268, 21.0, QgsUnitTypes.LayoutMillimeters))
        north_lbl.attemptResize(QgsLayoutSize(15, 4.5, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(north_lbl)

    MAP_X, MAP_Y, MAP_W, MAP_H = 8, 23, 210, 172
    m = QgsLayoutItemMap(layout)
    m.attemptMove(QgsLayoutPoint(MAP_X, MAP_Y, QgsUnitTypes.LayoutMillimeters))
    m.attemptResize(QgsLayoutSize(MAP_W, MAP_H, QgsUnitTypes.LayoutMillimeters))
    m.setExtent(extent)
    m.zoomToExtent(extent)
    m.setFrameEnabled(False)
    m.setBackgroundEnabled(False)

    display_layers = [joined_layer]
    if symbol_layer and symbol_layer.isValid():
        display_layers.insert(0, symbol_layer)
    
    m.setLayers(display_layers)
    m.setKeepLayerSet(True)
    layout.addLayoutItem(m)

    leg_x, leg_y = 220, 27
    leg_w = 71

    leg_head = QgsLayoutItemLabel(layout)
    apply_label_style(leg_head, "Legend",
                      QFont("Arial", 11, QFont.Bold), QColor("#000000"))
    leg_head.attemptMove(QgsLayoutPoint(leg_x, leg_y, QgsUnitTypes.LayoutMillimeters))
    leg_head.attemptResize(QgsLayoutSize(leg_w, 6, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(leg_head)

    item_y = leg_y + 7.5
    for _, _, hex_color, text_label in WARNING_COLOR_RAMP:
        patch = QgsLayoutItemShape(layout)
        patch.setShapeType(QgsLayoutItemShape.Rectangle)
        patch.attemptMove(QgsLayoutPoint(leg_x, item_y, QgsUnitTypes.LayoutMillimeters))
        patch.attemptResize(QgsLayoutSize(8, 5, QgsUnitTypes.LayoutMillimeters))
        style_shape(patch, hex_color, "#222222", 0.25)
        layout.addLayoutItem(patch)

        txt = QgsLayoutItemLabel(layout)
        apply_label_style(txt, text_label,
                          QFont("Arial", 9, QFont.Normal), QColor("#000000"),
                          v_align=Qt.AlignVCenter)
        txt.attemptMove(QgsLayoutPoint(leg_x + 11, item_y - 0.5, QgsUnitTypes.LayoutMillimeters))
        txt.attemptResize(QgsLayoutSize(leg_w - 11, 5.5, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(txt)

        item_y += 7.0

    box_x = 219
    box_w = 72
    box1_y = item_y + 5.0

    b1_h = 18.0
    s1_box = QgsLayoutItemShape(layout)
    s1_box.setShapeType(QgsLayoutItemShape.Rectangle)
    s1_box.attemptMove(QgsLayoutPoint(box_x, box1_y, QgsUnitTypes.LayoutMillimeters))
    s1_box.attemptResize(QgsLayoutSize(box_w, b1_h, QgsUnitTypes.LayoutMillimeters))
    style_shape(s1_box, "#008000", "#004D00", 0.35)
    layout.addLayoutItem(s1_box)

    wind_png = os.path.join(config.TEMPLATE_PATH, "symbols", "Wind_warning.png")
    windsock_svg = os.path.join(config.TEMPLATE_PATH, "symbols", "windsock.svg")
    wind_symbol_path = wind_png if os.path.exists(wind_png) else windsock_svg
    if os.path.exists(wind_symbol_path):
        ws_pic = QgsLayoutItemPicture(layout)
        ws_pic.setPicturePath(wind_symbol_path)
        ws_pic.attemptMove(QgsLayoutPoint(box_x + 1.5, box1_y + 2.0, QgsUnitTypes.LayoutMillimeters))
        ws_pic.attemptResize(QgsLayoutSize(13, 14, QgsUnitTypes.LayoutMillimeters))
        ws_pic.setResizeMode(ws_pic.Zoom)
        ws_pic.setFrameEnabled(False)
        ws_pic.setBackgroundEnabled(False)
        layout.addLayoutItem(ws_pic)

    s1_txt = QgsLayoutItemLabel(layout)
    apply_label_style(s1_txt, "Strong/Sustained surface wind\nwith speed reaching 30-40 kmph",
                      QFont("Arial", 7, QFont.Bold), QColor("#FFFFFF"),
                      v_align=Qt.AlignVCenter)
    s1_txt.attemptMove(QgsLayoutPoint(box_x + 15.0, box1_y + 1.0, QgsUnitTypes.LayoutMillimeters))
    s1_txt.attemptResize(QgsLayoutSize(box_w - 16.0, b1_h - 2.0, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(s1_txt)

    box2_y = box1_y + b1_h + 5.0
    b2_h = 25.0
    s2_box = QgsLayoutItemShape(layout)
    s2_box.setShapeType(QgsLayoutItemShape.Rectangle)
    s2_box.attemptMove(QgsLayoutPoint(box_x, box2_y, QgsUnitTypes.LayoutMillimeters))
    s2_box.attemptResize(QgsLayoutSize(box_w, b2_h, QgsUnitTypes.LayoutMillimeters))
    style_shape(s2_box, "#FFFF00", "#B2B200", 0.35)
    layout.addLayoutItem(s2_box)

    cloud_png = os.path.join(config.TEMPLATE_PATH, "symbols", "cloud.png")
    ts_wind_svg = os.path.join(config.TEMPLATE_PATH, "symbols", "thunderstorm_wind.svg")
    ts_symbol_path = cloud_png if os.path.exists(cloud_png) else ts_wind_svg
    if os.path.exists(ts_symbol_path):
        tsw_pic = QgsLayoutItemPicture(layout)
        tsw_pic.setPicturePath(ts_symbol_path)
        tsw_pic.attemptMove(QgsLayoutPoint(box_x + 1.5, box2_y + 3.0, QgsUnitTypes.LayoutMillimeters))
        tsw_pic.attemptResize(QgsLayoutSize(15, 18, QgsUnitTypes.LayoutMillimeters))
        tsw_pic.setResizeMode(tsw_pic.Zoom)
        tsw_pic.setFrameEnabled(False)
        tsw_pic.setBackgroundEnabled(False)
        layout.addLayoutItem(tsw_pic)

    s2_txt = QgsLayoutItemLabel(layout)
    apply_label_style(s2_txt, "Light Thunderstorm accompanied\nwith Lightning with Max surface\nwind speed 30-40 kmph",
                      QFont("Arial", 7, QFont.Bold), QColor("#000000"),
                      v_align=Qt.AlignVCenter)
    s2_txt.attemptMove(QgsLayoutPoint(box_x + 17.0, box2_y + 1.0, QgsUnitTypes.LayoutMillimeters))
    s2_txt.attemptResize(QgsLayoutSize(box_w - 18.0, b2_h - 2.0, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(s2_txt)

    footer = QgsLayoutItemLabel(layout)
    apply_label_style(footer, "India Meteorological Department — Meteorological Centre Hyderabad  |  Ph: 040-27908506  |  Website: mausam.imd.gov.in/hyderabad",
                      QFont("Arial", 6, QFont.Normal), QColor(60, 60, 60),
                      h_align=Qt.AlignCenter, v_align=Qt.AlignVCenter)
    footer.attemptMove(QgsLayoutPoint(5, 203.5, QgsUnitTypes.LayoutMillimeters))
    footer.attemptResize(QgsLayoutSize(287, 4.0, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(footer)

    return layout

def generate_thunderstorm_warning_maps(
    project: QgsProject,
    warning_gpkg: str,
    output_dir: str,
    date_str: str = ""
) -> List[str]:
    if not os.path.exists(warning_gpkg):
        print(f"[THUNDERSTORM WARN ERR] Warning GPKG missing: {warning_gpkg}")
        return []

    layer = QgsVectorLayer(warning_gpkg, "Thunderstorm_Warnings", "ogr")
    if not layer.isValid():
        print(f"[THUNDERSTORM WARN ERR] Layer invalid: {warning_gpkg}")
        return []

    project.addMapLayer(layer)
    generated_files = []
    os.makedirs(output_dir, exist_ok=True)

    for day in range(1, 6):
        field_name = f"warning{day}"
        apply_warning_style(layer, field_name)

        sym_layer = create_weather_symbols_layer(project, layer, field_name)

        layout = build_thunderstorm_layout(project, layer, day_num=day, date_str=date_str, symbol_layer=sym_layer)

        base_name = f"thunderstorm_warning_day{day}"
        png_path = os.path.join(output_dir, f"{base_name}.png")
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

        if os.path.exists(png_path):
            try:
                os.remove(png_path)
            except OSError:
                pass
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError:
                pass

        exporter = QgsLayoutExporter(layout)

        img_settings = QgsLayoutExporter.ImageExportSettings()
        img_settings.dpi = 300
        exporter.exportToImage(png_path, img_settings)

        pdf_settings = QgsLayoutExporter.PdfExportSettings()
        pdf_settings.dpi = 300
        exporter.exportToPdf(pdf_path, pdf_settings)

        if sym_layer:
            project.removeMapLayer(sym_layer.id())

        generated_files.extend([png_path, pdf_path])
        print(f"[THUNDERSTORM WARN OK] Generated Day {day} Thunderstorm Map -> PNG/PDF (300 DPI)")

    return generated_files

if __name__ == "__main__":
    from qgis.core import QgsApplication
    QgsApplication.setPrefixPath(getattr(config, "QGIS_PREFIX", config.QGIS_ROOT), True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    try:
        project = QgsProject.instance()
        out_folder = config.OUTPUT_PATH
        warning_gpkg = os.path.join(out_folder, "WarningJoined.gpkg")
        today_str = datetime.date.today().strftime('%d-%m-%Y')
        if os.path.exists(warning_gpkg):
            generate_thunderstorm_warning_maps(project, warning_gpkg, out_folder, today_str)
        else:
            print(f"[THUNDERSTORM WARN ERR] WarningJoined.gpkg not found at {warning_gpkg}")
    finally:
        qgs.exitQgis()
