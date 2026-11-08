import os
import sys
import datetime
import warnings
from typing import List, Tuple, Dict, Optional

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
    QgsSingleSymbolRenderer,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProperty,
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
)
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QColor, QFont

import config

TMAX_COLOR_RAMP = [
    (0.0,  40.9, "#008000", "No Warning", "(<= 40 °C)"),
    (41.0, 45.9, "#FFFF00", "Be Alert", "(41-45 °C)"),
    (46.0, 47.9, "#FF8000", "Be Prepared", "(46-47 °C)"),
    (48.0, 99.0, "#FF0000", "Warning", "(> 47 °C)"),
]

TMIN_COLOR_RAMP = [
    (-99.0,  4.9, "#FF0000", "Warning", "(< 5 °C)"),
    (5.0,   10.9, "#FF8000", "Alert", "(5-10 °C)"),
    (11.0,  15.9, "#FFFF00", "Watch", "(11-15 °C)"),
    (16.0,  99.0, "#008000", "No Warning", "(> 15 °C)"),
]

DISTRICT_DIRECTORY_3COL = [
    [
        ("ADL", "Adilabad"),
        ("BDDK", "Bhadradri Kothagudem"),
        ("HYD", "Hyderabad"),
        ("JGTL", "Jagitial"),
        ("JGLG", "Jogulamba Gadwal"),
        ("JNG", "Jangaon"),
        ("JSKB", "Jayashankar Bhupalpally"),
        ("KMR", "Kamareddy"),
        ("KRM", "Karimnagar"),
        ("KHM", "Khammam"),
        ("KMB", "Komaram Bheem"),
    ],
    [
        ("MBN", "Mahabubnagar"),
        ("MBB", "Mahabubabad"),
        ("MCRL", "Mancherial"),
        ("MDK", "Medak"),
        ("MDCM", "Medchal Malkajgiri"),
        ("MLG", "Mulugu"),
        ("NGK", "Nagarkurnool"),
        ("NLG", "Nalgonda"),
        ("NRPT", "Narayanpet"),
        ("NRL", "Nirmal"),
        ("NZB", "Nizamabad"),
    ],
    [
        ("PPL", "Peddapalli"),
        ("RJNS", "Rajanna Sircilla"),
        ("RR", "Ranga Reddy"),
        ("SGR", "Sangareddy"),
        ("SDP", "Siddipet"),
        ("SRPT", "Suryapet"),
        ("VKB", "Vikarabad"),
        ("WNP", "Wanaparthy"),
        ("WRGR", "Warangal"),
        ("WRGU", "Hanumakonda"),
        ("YDDB", "Yadadri Bhuvanagiri"),
    ],
]

PAGE_W = 297.0
PAGE_H = 210.0
TELANGANA_EXTENT = QgsRectangle(76.40, 15.54, 82.13, 20.20)

LOGO_X, LOGO_Y, LOGO_W, LOGO_H = 12.0, 3.5, 21.0, 21.0
LOGO_LBL_X, LOGO_LBL_Y, LOGO_LBL_W, LOGO_LBL_H = 2.0, 25.0, 42.0, 8.0

NORTH_X, NORTH_Y, NORTH_W, NORTH_H = 268.0, 3.5, 15.0, 17.0
NORTH_LBL_X, NORTH_LBL_Y, NORTH_LBL_W, NORTH_LBL_H = 268.0, 21.0, 15.0, 5.0

TITLE_X, TITLE_Y, TITLE_W = 46.0, 3.5, 206.0
DIVIDER_Y = 34.0

GRID_MARGIN_L = 8.0
GRID_MARGIN_R = 8.0
COL_W = 89.0
GUTTER_X = 7.0
COL_X = [
    GRID_MARGIN_L,
    GRID_MARGIN_L + COL_W + GUTTER_X,
    GRID_MARGIN_L + 2 * (COL_W + GUTTER_X),
]

PANEL_H = 78.0
GUTTER_Y = 5.0

ROW1_Y = 36.5
ROW2_Y = ROW1_Y + PANEL_H + GUTTER_Y

CELL6_X = COL_X[2]
CELL6_Y = ROW2_Y
CELL6_W = COL_W
CELL6_H = PANEL_H

FOOTER_DIV_Y = 202.0
FOOTER_Y = 202.5
FOOTER_H = 5.0
FOOTER_W = PAGE_W - 16.0
FOOTER_X = 8.0
FOOTER_TEXT = (
    "India Meteorological Department — Meteorological Centre Hyderabad  |  "
    "Ph: 040-27908506  |  Website: mausam.imd.gov.in/hyderabad"
)

def style_shape(shape: QgsLayoutItemShape, fill_hex: str, stroke_hex: str, stroke_width: float = 0.35) -> None:
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

def apply_temp_graduated_style(layer: QgsVectorLayer, field_name: str, forecast_type: str = "Maximum") -> None:
    is_max = forecast_type.lower().startswith("max")
    ramp = TMAX_COLOR_RAMP if is_max else TMIN_COLOR_RAMP
    ranges = []
    for min_val, max_val, hex_color, cat_name, temp_range in ramp:
        symbol = QgsFillSymbol.createSimple({
            "color": hex_color,
            "outline_color": "#2C3E50",
            "outline_width": "0.30",
        })
        ranges.append(QgsRendererRange(min_val, max_val, symbol, f"{cat_name} {temp_range}"))

    renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
    layer.setRenderer(renderer)
    layer.setLabelsEnabled(False)
    layer.triggerRepaint()

def create_curated_district_label_layer() -> QgsVectorLayer:
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "District_Labels", "memory")
    dp = layer.dataProvider()
    dp.addAttributes([QgsField("code", QVariant.String)])
    layer.updateFields()

    coords = [
        (78.560, 19.520, "ADL"),
        (79.420, 19.360, "KMB"),
        (78.320, 19.110, "NRL"),
        (79.520, 18.990, "MCRL"),
        (78.160, 18.780, "NZB"),
        (78.880, 18.880, "JGTL"),
        (79.460, 18.720, "PPL"),
        (77.940, 18.280, "KMR"),
        (78.700, 18.420, "RJNS"),
        (79.160, 18.240, "KRM"),
        (79.940, 18.520, "JSKB"),
        (80.360, 18.250, "MLG"),
        (77.820, 17.780, "SGR"),
        (78.240, 18.020, "MDK"),
        (78.820, 18.080, "SDP"),
        (79.380, 18.060, "WRGU"),
        (79.780, 17.880, "WRGR"),
        (79.380, 17.650, "JNG"),
        (78.480, 17.650, "MDCM"),
        (79.080, 17.420, "YDDB"),
        (80.080, 17.580, "MBB"),
        (80.700, 17.690, "BDDK"),
        (78.467, 17.380, "HYD"),
        (77.700, 17.220, "VKB"),
        (78.300, 16.980, "RR"),
        (78.680, 16.420, "NGK"),
        (79.760, 17.060, "SRPT"),
        (80.360, 17.180, "KHM"),
        (78.100, 16.750, "MBN"),
        (78.020, 16.360, "WNP"),
        (79.190, 16.850, "NLG"),
        (77.780, 15.940, "JGLG"),
        (77.520, 16.650, "NRPT"),
    ]

    features = []
    for lon, lat, code in coords:
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        feat.setAttributes([code])
        features.append(feat)
    dp.addFeatures(features)

    sym = QgsMarkerSymbol.createSimple({"size": "0", "color": "0,0,0,0", "outline_color": "0,0,0,0"})
    layer.setRenderer(QgsSingleSymbolRenderer(sym))

    pal = QgsPalLayerSettings()
    pal.fieldName = "code"
    pal.isExpression = False
    pal.placement = Qgis.LabelPlacement.OverPoint if hasattr(Qgis, "LabelPlacement") else QgsPalLayerSettings.OverPoint
    pal.displayAll = True
    pal.priority = 10

    fmt = QgsTextFormat()
    fmt.setFont(QFont("Arial", 6, QFont.Bold))
    fmt.setSize(6.2)
    fmt.setSizeUnit(QgsUnitTypes.RenderPoints)
    fmt.setColor(QColor("#0F172A"))

    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(0.55)
    buf.setColor(QColor("#FFFFFF"))
    fmt.setBuffer(buf)

    pal.setFormat(fmt)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)
    layer.triggerRepaint()
    return layer

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

def build_5day_temp_grid_layout(
    project: QgsProject,
    day_layers: List[QgsVectorLayer],
    label_layer: QgsVectorLayer,
    forecast_type: str = "Maximum",
    date_str: str = ""
) -> QgsPrintLayout:
    is_max = forecast_type.lower().startswith("max")
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(f"5Day_{forecast_type}_Temp_Grid")
    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(PAGE_W, PAGE_H, QgsUnitTypes.LayoutMillimeters))

    imd_logo = os.path.join(config.TEMPLATE_PATH, "IMD_LOGO.png")
    if os.path.exists(imd_logo):
        logo = QgsLayoutItemPicture(layout)
        logo.setPicturePath(imd_logo)
        logo.attemptMove(QgsLayoutPoint(LOGO_X, LOGO_Y, QgsUnitTypes.LayoutMillimeters))
        logo.attemptResize(QgsLayoutSize(LOGO_W, LOGO_H, QgsUnitTypes.LayoutMillimeters))
        logo.setResizeMode(logo.Zoom)
        logo.setFrameEnabled(False)
        logo.setBackgroundEnabled(False)
        layout.addLayoutItem(logo)

        logo_lbl = QgsLayoutItemLabel(layout)
        apply_label_style(logo_lbl, "Meteorological Centre\nHyderabad", QFont("Arial", 8, QFont.Bold), QColor("#000000"), h_align=Qt.AlignHCenter, v_align=Qt.AlignTop)
        logo_lbl.attemptMove(QgsLayoutPoint(LOGO_LBL_X, LOGO_LBL_Y, QgsUnitTypes.LayoutMillimeters))
        logo_lbl.attemptResize(QgsLayoutSize(LOGO_LBL_W, LOGO_LBL_H, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(logo_lbl)

    if os.path.exists(config.NORTH_ARROW_SVG):
        north = QgsLayoutItemPicture(layout)
        north.setPicturePath(config.NORTH_ARROW_SVG)
        north.attemptMove(QgsLayoutPoint(NORTH_X, NORTH_Y, QgsUnitTypes.LayoutMillimeters))
        north.attemptResize(QgsLayoutSize(NORTH_W, NORTH_H, QgsUnitTypes.LayoutMillimeters))
        north.setResizeMode(north.Zoom)
        north.setFrameEnabled(False)
        north.setBackgroundEnabled(False)
        layout.addLayoutItem(north)

        north_lbl = QgsLayoutItemLabel(layout)
        apply_label_style(north_lbl, "N", QFont("Arial", 8, QFont.Bold), QColor("#000000"), h_align=Qt.AlignCenter)
        north_lbl.attemptMove(QgsLayoutPoint(NORTH_LBL_X, NORTH_LBL_Y, QgsUnitTypes.LayoutMillimeters))
        north_lbl.attemptResize(QgsLayoutSize(NORTH_LBL_W, NORTH_LBL_H, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(north_lbl)

    header_dept = QgsLayoutItemLabel(layout)
    apply_label_style(header_dept, "INDIA METEOROLOGICAL DEPARTMENT", QFont("Arial", 14, QFont.Bold), QColor("#0F172A"), h_align=Qt.AlignCenter)
    header_dept.attemptMove(QgsLayoutPoint(TITLE_X, TITLE_Y, QgsUnitTypes.LayoutMillimeters))
    header_dept.attemptResize(QgsLayoutSize(TITLE_W, 7.0, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(header_dept)

    sub_title = QgsLayoutItemLabel(layout)
    apply_label_style(sub_title, f"{'Maximum' if is_max else 'Minimum'} Temperature Forecast for Next 5 Days for Districts of Telangana", QFont("Arial", 10, QFont.Bold), QColor("#B91C1C" if is_max else "#1D4ED8"), h_align=Qt.AlignCenter)
    sub_title.attemptMove(QgsLayoutPoint(TITLE_X, TITLE_Y + 7.5, QgsUnitTypes.LayoutMillimeters))
    sub_title.attemptResize(QgsLayoutSize(TITLE_W, 6.0, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(sub_title)

    dt_str = date_str or datetime.date.today().strftime('%d-%m-%Y')
    date_lbl = QgsLayoutItemLabel(layout)
    apply_label_style(date_lbl, f"Meteorological Centre, Hyderabad  |  Issue Date: {dt_str}", QFont("Arial", 8, QFont.Bold), QColor("#4B5563"), h_align=Qt.AlignCenter)
    date_lbl.attemptMove(QgsLayoutPoint(TITLE_X, TITLE_Y + 14.0, QgsUnitTypes.LayoutMillimeters))
    date_lbl.attemptResize(QgsLayoutSize(TITLE_W, 5.0, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(date_lbl)

    rule = QgsLayoutItemShape(layout)
    rule.setShapeType(QgsLayoutItemShape.Rectangle)
    rule.attemptMove(QgsLayoutPoint(GRID_MARGIN_L, DIVIDER_Y, QgsUnitTypes.LayoutMillimeters))
    rule.attemptResize(QgsLayoutSize(PAGE_W - 2 * GRID_MARGIN_L, 0.35, QgsUnitTypes.LayoutMillimeters))
    style_shape(rule, "#CBD5E1", "#CBD5E1", 0.0)
    layout.addLayoutItem(rule)

    grid_coords = [
        (COL_X[0], ROW1_Y, "DAY 1 FORECAST"),
        (COL_X[1], ROW1_Y, "DAY 2 FORECAST"),
        (COL_X[2], ROW1_Y, "DAY 3 FORECAST"),
        (COL_X[0], ROW2_Y, "DAY 4 FORECAST"),
        (COL_X[1], ROW2_Y, "DAY 5 FORECAST"),
    ]

    for idx, (x, y, day_title) in enumerate(grid_coords, start=1):
        card = QgsLayoutItemShape(layout)
        card.setShapeType(QgsLayoutItemShape.Rectangle)
        card.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))
        card.attemptResize(QgsLayoutSize(COL_W, PANEL_H, QgsUnitTypes.LayoutMillimeters))
        style_shape(card, "#FFFFFF", "#CBD5E1", 0.30)
        layout.addLayoutItem(card)

        badge_bg = QgsLayoutItemShape(layout)
        badge_bg.setShapeType(QgsLayoutItemShape.Rectangle)
        badge_bg.attemptMove(QgsLayoutPoint(x + 1.0, y + 1.0, QgsUnitTypes.LayoutMillimeters))
        badge_bg.attemptResize(QgsLayoutSize(COL_W - 2.0, 5.2, QgsUnitTypes.LayoutMillimeters))
        style_shape(badge_bg, "#F8FAFC", "#E2E8F0", 0.20)
        layout.addLayoutItem(badge_bg)

        lbl = QgsLayoutItemLabel(layout)
        apply_label_style(lbl, day_title, QFont("Arial", 8, QFont.Bold), QColor("#1E293B"), h_align=Qt.AlignCenter, v_align=Qt.AlignVCenter)
        lbl.attemptMove(QgsLayoutPoint(x + 1.2, y + 1.1, QgsUnitTypes.LayoutMillimeters))
        lbl.attemptResize(QgsLayoutSize(COL_W - 2.4, 5.0, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(lbl)

        m = QgsLayoutItemMap(layout)
        m.attemptMove(QgsLayoutPoint(x + 1.0, y + 6.6, QgsUnitTypes.LayoutMillimeters))
        m.attemptResize(QgsLayoutSize(COL_W - 2.0, PANEL_H - 7.6, QgsUnitTypes.LayoutMillimeters))
        m.setExtent(TELANGANA_EXTENT)
        m.zoomToExtent(TELANGANA_EXTENT)
        m.setFrameEnabled(False)
        m.setBackgroundEnabled(False)
        m.setLayers([label_layer, day_layers[idx - 1]])
        m.setKeepLayerSet(True)
        layout.addLayoutItem(m)

    c6_card = QgsLayoutItemShape(layout)
    c6_card.setShapeType(QgsLayoutItemShape.Rectangle)
    c6_card.attemptMove(QgsLayoutPoint(CELL6_X, CELL6_Y, QgsUnitTypes.LayoutMillimeters))
    c6_card.attemptResize(QgsLayoutSize(CELL6_W, CELL6_H, QgsUnitTypes.LayoutMillimeters))
    style_shape(c6_card, "#FFFFFF", "#CBD5E1", 0.35)
    layout.addLayoutItem(c6_card)

    leg_header = QgsLayoutItemLabel(layout)
    apply_label_style(leg_header, f"{'HEATWAVE' if is_max else 'COLD WAVE'} WARNING SCALE ({'TMAX' if is_max else 'TMIN'})", QFont("Arial", 7, QFont.Bold), QColor("#0F172A"), h_align=Qt.AlignCenter)
    leg_header.attemptMove(QgsLayoutPoint(CELL6_X + 2.0, CELL6_Y + 1.5, QgsUnitTypes.LayoutMillimeters))
    leg_header.attemptResize(QgsLayoutSize(CELL6_W - 4.0, 4.0, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(leg_header)

    leg_div1 = QgsLayoutItemShape(layout)
    leg_div1.setShapeType(QgsLayoutItemShape.Rectangle)
    leg_div1.attemptMove(QgsLayoutPoint(CELL6_X + 3.5, CELL6_Y + 5.8, QgsUnitTypes.LayoutMillimeters))
    leg_div1.attemptResize(QgsLayoutSize(CELL6_W - 7.0, 0.25, QgsUnitTypes.LayoutMillimeters))
    style_shape(leg_div1, "#E2E8F0", "#E2E8F0", 0.0)
    layout.addLayoutItem(leg_div1)

    ramp = TMAX_COLOR_RAMP if is_max else TMIN_COLOR_RAMP
    PATCH_W = 13.0
    PATCH_H = 3.8
    scale_top = CELL6_Y + 6.8
    row_pitch = 4.8

    for i, (_, _, hex_color, cat_name, temp_range) in enumerate(ramp):
        py = scale_top + i * row_pitch

        patch = QgsLayoutItemShape(layout)
        patch.setShapeType(QgsLayoutItemShape.Rectangle)
        patch.attemptMove(QgsLayoutPoint(CELL6_X + 3.5, py, QgsUnitTypes.LayoutMillimeters))
        patch.attemptResize(QgsLayoutSize(PATCH_W, PATCH_H, QgsUnitTypes.LayoutMillimeters))
        style_shape(patch, hex_color, "#334155", 0.20)
        layout.addLayoutItem(patch)

        lbl_cat = QgsLayoutItemLabel(layout)
        apply_label_style(lbl_cat, cat_name, QFont("Arial", 6, QFont.Bold), QColor("#1E293B"), v_align=Qt.AlignVCenter)
        lbl_cat.attemptMove(QgsLayoutPoint(CELL6_X + 3.5 + PATCH_W + 2.5, py, QgsUnitTypes.LayoutMillimeters))
        lbl_cat.attemptResize(QgsLayoutSize(34.0, PATCH_H, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(lbl_cat)

        lbl_val = QgsLayoutItemLabel(layout)
        apply_label_style(lbl_val, temp_range, QFont("Arial", 6, QFont.Normal), QColor("#475569"), h_align=Qt.AlignRight, v_align=Qt.AlignVCenter)
        lbl_val.attemptMove(QgsLayoutPoint(CELL6_X + CELL6_W - 35.0, py, QgsUnitTypes.LayoutMillimeters))
        lbl_val.attemptResize(QgsLayoutSize(31.5, PATCH_H, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(lbl_val)

    dir_top = CELL6_Y + 26.8

    dir_div = QgsLayoutItemShape(layout)
    dir_div.setShapeType(QgsLayoutItemShape.Rectangle)
    dir_div.attemptMove(QgsLayoutPoint(CELL6_X + 3.5, dir_top, QgsUnitTypes.LayoutMillimeters))
    dir_div.attemptResize(QgsLayoutSize(CELL6_W - 7.0, 0.25, QgsUnitTypes.LayoutMillimeters))
    style_shape(dir_div, "#CBD5E1", "#CBD5E1", 0.0)
    layout.addLayoutItem(dir_div)

    dir_header = QgsLayoutItemLabel(layout)
    apply_label_style(dir_header, "TELANGANA DISTRICTS DIRECTORY (33)", QFont("Arial", 6, QFont.Bold), QColor("#0F172A"), h_align=Qt.AlignCenter)
    dir_header.attemptMove(QgsLayoutPoint(CELL6_X + 2.0, dir_top + 1.0, QgsUnitTypes.LayoutMillimeters))
    dir_header.attemptResize(QgsLayoutSize(CELL6_W - 4.0, 3.5, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(dir_header)

    dir_col_w = (CELL6_W - 7.0) / 3.0
    dir_body_top = dir_top + 4.8
    dir_row_pitch = 4.10

    for c_idx, col_items in enumerate(DISTRICT_DIRECTORY_3COL):
        col_x = CELL6_X + 3.5 + c_idx * dir_col_w
        for r_idx, (code, full_name) in enumerate(col_items):
            ry = dir_body_top + r_idx * dir_row_pitch

            code_lbl = QgsLayoutItemLabel(layout)
            apply_label_style(code_lbl, f"{code}:", QFont("Arial", 5, QFont.Bold), QColor("#0F172A"))
            code_lbl.attemptMove(QgsLayoutPoint(col_x, ry, QgsUnitTypes.LayoutMillimeters))
            code_lbl.attemptResize(QgsLayoutSize(8.8, 3.4, QgsUnitTypes.LayoutMillimeters))
            layout.addLayoutItem(code_lbl)

            name_lbl = QgsLayoutItemLabel(layout)
            apply_label_style(name_lbl, full_name, QFont("Arial", 5, QFont.Normal), QColor("#1E293B"))
            name_lbl.attemptMove(QgsLayoutPoint(col_x + 8.8, ry, QgsUnitTypes.LayoutMillimeters))
            name_lbl.attemptResize(QgsLayoutSize(dir_col_w - 8.8, 3.4, QgsUnitTypes.LayoutMillimeters))
            layout.addLayoutItem(name_lbl)

    footer_div = QgsLayoutItemShape(layout)
    footer_div.setShapeType(QgsLayoutItemShape.Rectangle)
    footer_div.attemptMove(QgsLayoutPoint(FOOTER_X, FOOTER_DIV_Y, QgsUnitTypes.LayoutMillimeters))
    footer_div.attemptResize(QgsLayoutSize(FOOTER_W, 0.35, QgsUnitTypes.LayoutMillimeters))
    style_shape(footer_div, "#CBD5E1", "#CBD5E1", 0.0)
    layout.addLayoutItem(footer_div)

    footer_box = QgsLayoutItemShape(layout)
    footer_box.setShapeType(QgsLayoutItemShape.Rectangle)
    footer_box.attemptMove(QgsLayoutPoint(FOOTER_X, FOOTER_Y, QgsUnitTypes.LayoutMillimeters))
    footer_box.attemptResize(QgsLayoutSize(FOOTER_W, FOOTER_H, QgsUnitTypes.LayoutMillimeters))
    style_shape(footer_box, "#F8FAFC", "#E2E8F0", 0.25)
    layout.addLayoutItem(footer_box)

    footer_lbl = QgsLayoutItemLabel(layout)
    apply_label_style(footer_lbl, FOOTER_TEXT, QFont("Arial", 6, QFont.Bold), QColor("#475569"),
                      h_align=Qt.AlignCenter, v_align=Qt.AlignVCenter)
    footer_lbl.attemptMove(QgsLayoutPoint(FOOTER_X + 2.0, FOOTER_Y + 0.5, QgsUnitTypes.LayoutMillimeters))
    footer_lbl.attemptResize(QgsLayoutSize(FOOTER_W - 4.0, FOOTER_H - 1.0, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(footer_lbl)

    return layout

def generate_5day_temp_grid_map(
    project: QgsProject,
    joined_gpkg: str,
    output_dir: str,
    forecast_type: str = "Maximum",
    date_str: str = ""
) -> List[str]:
    if not os.path.exists(joined_gpkg):
        print(f"[5DAY TEMP GRID ERR] Joined GPKG missing: {joined_gpkg}")
        return []

    project.removeAllMapLayers()
    prefix = "tmax" if forecast_type.lower().startswith("max") else "tmin"

    day_layers: List[QgsVectorLayer] = []
    for day_num in range(1, 6):
        layer = QgsVectorLayer(joined_gpkg, f"Joined_{forecast_type}_Day{day_num}", "ogr")
        if not layer.isValid():
            print(f"[5DAY TEMP GRID ERR] Layer invalid: {joined_gpkg}")
            return []
        apply_temp_graduated_style(layer, f"{prefix}{day_num}", forecast_type)
        project.addMapLayer(layer)
        day_layers.append(layer)

    label_layer = create_curated_district_label_layer()
    project.addMapLayer(label_layer)

    layout = build_5day_temp_grid_layout(project, day_layers, label_layer, forecast_type, date_str)

    os.makedirs(output_dir, exist_ok=True)
    out_name = "max_temp_5day_summary" if prefix == "tmax" else "min_temp_5day_summary"
    png_path = os.path.join(output_dir, f"{out_name}.png")
    pdf_path = os.path.join(output_dir, f"{out_name}.pdf")

    for p in (png_path, pdf_path):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass

    exporter = QgsLayoutExporter(layout)

    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    exporter.exportToImage(png_path, settings)

    pdf_settings = QgsLayoutExporter.PdfExportSettings()
    pdf_settings.dpi = 300
    exporter.exportToPdf(pdf_path, pdf_settings)

    print(f"[5DAY TEMP GRID OK] Generated 5-Day {forecast_type} Temperature Grid Summary:")
    print(f"  + PNG: {png_path}")
    print(f"  + PDF: {pdf_path}")

    return [png_path, pdf_path]

if __name__ == "__main__":
    from qgis.core import QgsApplication
    QgsApplication.setPrefixPath(getattr(config, "QGIS_PREFIX", config.QGIS_ROOT), True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    try:
        project = QgsProject.instance()
        out_folder = config.OUTPUT_PATH
        temp_gpkg = os.path.join(out_folder, "TempJoined.gpkg")
        today_str = datetime.date.today().strftime('%d-%m-%Y')
        if os.path.exists(temp_gpkg):
            generate_5day_temp_grid_map(project, temp_gpkg, out_folder, "Maximum", today_str)
            generate_5day_temp_grid_map(project, temp_gpkg, out_folder, "Minimum", today_str)
        else:
            print(f"[5DAY TEMP GRID ERR] TempJoined.gpkg not found at {temp_gpkg}")
    finally:
        qgs.exitQgis()