import os
import re
import warnings
from typing import Dict, List, Tuple, Optional, Any

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import openpyxl

DISTRICT_REF_TABLE = [
    ("Adilabad", "Adilabad", "ADL", 19.65, 78.53),
    ("Komaram Bheem", "KomaramBheem", "KMB", 19.32656, 79.20103),
    ("Mancherial", "Mancherial", "MCRL", 19.00801, 79.60121),
    ("Nirmal", "Nirmal", "NRL", 19.09362, 78.44297),
    ("Nizamabad", "Nizamabad", "NZB", 18.71235, 78.2165),
    ("Jagtial", "Jagitial", "JGTL", 18.86, 78.84),
    ("Rajanna Sircilla", "RajannaSiricilla", "RJNS", 18.42, 78.76),
    ("Karimnagar", "Karimnagar", "KRM", 18.36095, 79.21795),
    ("Peddapalli", "Peddapalle", "PPL", 18.63, 79.42),
    ("Jayashankar Bhupalpally", "JayashankarBhupalapalle", "JSKB", 18.50729, 79.91179),
    ("Mulugu", "Mulugu", "MLG", 18.19, 79.94),
    ("Bhadradri Kothagudem", "Bkothagudem", "BDDK", 17.83, 80.83),
    ("Khammam", "Khammam", "KHM", 17.24005, 80.2622),
    ("Nalgonda", "Nalgonda", "NLG", 16.93842, 79.18311),
    ("Suryapet", "Suryapet", "SRPT", 17.16887, 79.72066),
    ("Mahabubabad", "Mahabubabad", "MBB", 17.62629, 79.98745),
    ("Warangal (R)", "Warangal", "WRGR", 17.9324, 79.78437),
    ("Hanumakonda(U", "Hanumakonda", "WRGU", 18.03792, 79.4698),
    ("Jangaon", "Jangaon", "JNG", 17.76317, 79.27668),
    ("Siddipet", "Siddipet", "SDP", 18.0429, 78.83867),
    ("Yadadri Bhuvanagiri", "yadadribhuvanagiri", "YDDB", 17.59, 78.94),
    ("Ranga Reddy", "Rangareddy", "RR", 17.13, 78.32),
    ("Hyderabad", "Hyderabad", "HYD", 17.39, 78.47),
    ("Medchal Malkajgiri", "MedchalMalkajgiri", "MDCM", 17.56855, 78.5461),
    ("Vikarabad", "Vikarabad", "VKB", 17.28036, 77.74764),
    ("Sangareddy", "SangaReddy", "SGR", 17.77213, 77.84718),
    ("Medak", "Medak", "MDK", 17.96475, 78.29216),
    ("Kamareddy", "Kamareddy", "KMR", 18.31118, 78.03533),
    ("Mahbubnagar", "MahabubNagar", "MBN", 16.77516, 77.99053),
    ("Nagarkurnool", "NagarKurnool", "NGK", 16.30231, 78.56791),
    ("Wanaparthy", "Wanaparthy", "WNP", 16.3048, 78.02438),
    ("Narayanpet", "Narayanpet", "NRPT", 16.74, 77.49),
    ("Jogulamba Gadwal", "JogulambaGadwal", "JGLG", 16.10222, 77.71976),
]

CANONICAL_DISTRICTS = {
    "adilabad": ("Adilabad", "ADL", 19.65, 78.53),
    "komarambheem": ("Kumurambheem Asifabad", "KMB", 19.32656, 79.20103),
    "kumurambheemasifabad": ("Kumurambheem Asifabad", "KMB", 19.32656, 79.20103),
    "komarambheemasifabad": ("Kumurambheem Asifabad", "KMB", 19.32656, 79.20103),
    "mancherial": ("Mancherial", "MCRL", 19.00801, 79.60121),
    "nirmal": ("Nirmal", "NRL", 19.09362, 78.44297),
    "nizamabad": ("Nizamabad", "NZB", 18.71235, 78.2165),
    "jagtial": ("Jagtial", "JGTL", 18.86, 78.84),
    "jagitial": ("Jagtial", "JGTL", 18.86, 78.84),
    "rajannasircilla": ("Rajanna Sircilla", "RJNS", 18.42, 78.76),
    "rajannasiricilla": ("Rajanna Sircilla", "RJNS", 18.42, 78.76),
    "karimnagar": ("Karimnagar", "KRM", 18.36095, 79.21795),
    "peddapalli": ("Peddapalli", "PPL", 18.63, 79.42),
    "peddapalle": ("Peddapalli", "PPL", 18.63, 79.42),
    "jayashankarbhupalpally": ("Jayashankar Bhupalpally", "JSKB", 18.50729, 79.91179),
    "jayashankarbhupalapalle": ("Jayashankar Bhupalpally", "JSKB", 18.50729, 79.91179),
    "mulugu": ("Mulugu", "MLG", 18.19, 79.94),
    "bhadradrikothagudem": ("Bhadradri Kothagudem", "BDDK", 17.83, 80.83),
    "bkothagudem": ("Bhadradri Kothagudem", "BDDK", 17.83, 80.83),
    "khammam": ("Khammam", "KHM", 17.24005, 80.2622),
    "nalgonda": ("Nalgonda", "NLG", 16.93842, 79.18311),
    "suryapet": ("Suryapet", "SRPT", 17.16887, 79.72066),
    "mahabubabad": ("Mahabubabad", "MBB", 17.62629, 79.98745),
    "warangal": ("Warangal", "WRGR", 17.9324, 79.78437),
    "warangalr": ("Warangal", "WRGR", 17.9324, 79.78437),
    "hanumakonda": ("Hanumakonda", "WRGU", 18.03792, 79.4698),
    "hanumakondau": ("Hanumakonda", "WRGU", 18.03792, 79.4698),
    "jangaon": ("Jangoan", "JNG", 17.76317, 79.27668),
    "jangoan": ("Jangoan", "JNG", 17.76317, 79.27668),
    "siddipet": ("Siddipet", "SDP", 18.0429, 78.83867),
    "yadadribhuvanagiri": ("Yadadri Bhuvanagiri", "YDDB", 17.59, 78.94),
    "rangareddy": ("Rangareddy", "RR", 17.13, 78.32),
    "hyderabad": ("Hyderabad", "HYD", 17.39, 78.47),
    "medchalmalkajgiri": ("Medchal Malkajgiri", "MDCM", 17.56855, 78.5461),
    "vikarabad": ("Vikarabad", "VKB", 17.28036, 77.74764),
    "sangareddy": ("Sangareddy", "SGR", 17.77213, 77.84718),
    "medak": ("Medak", "MDK", 17.96475, 78.29216),
    "kamareddy": ("Kamareddy", "KMR", 18.31118, 78.03533),
    "mahbubnagar": ("Mahabubnagar", "MBN", 16.77516, 77.99053),
    "nagarkurnool": ("Nagarkurnool", "NGK", 16.30231, 78.56791),
    "wanaparthy": ("Wanaparthy", "WNP", 16.3048, 78.02438),
    "narayanpet": ("Narayanpet", "NRPT", 16.74, 77.49),
    "jogulambagadwal": ("Jogulamba Gadwal", "JGLG", 16.10222, 77.71976),
}

def _normalize_name(name: str) -> str:
    return re.sub(r"[\s\-_.,()\\']+", "", str(name)).lower()

_NORM_DIST_MAP = {_normalize_name(item[0]): item for item in DISTRICT_REF_TABLE}

def match_district_meta(raw_dist_name: str) -> Tuple[str, str, float, float]:
    if not raw_dist_name or str(raw_dist_name).strip() == "":
        return ("Unknown", "DIST", 18.0, 79.0)

    norm_key = _normalize_name(raw_dist_name)
    if norm_key in CANONICAL_DISTRICTS:
        return CANONICAL_DISTRICTS[norm_key]

    ref_data = _NORM_DIST_MAP.get(norm_key)
    if not ref_data:
        for k, item in _NORM_DIST_MAP.items():
            if k in norm_key or norm_key in k:
                ref_data = item
                break

    if not ref_data:
        return (str(raw_dist_name).strip(), "DIST", 18.0, 79.0)

    _, std_name, code, lat, lon = ref_data
    return (std_name, code, lat, lon)

def parse_spatial_code(val: Optional[Any]) -> int:
    if val is None:
        return 1
    s = str(val).strip().upper()
    if not s or "DRY" in s or "NO RAIN" in s or s in ("NONE", "NIL", "-"):
        return 1
    if "ISOL" in s:
        return 2
    if "SCT" in s or "FEW" in s:
        return 3
    if "FWS" in s or "MANY" in s:
        return 4
    if "WS" in s or "MOST" in s:
        return 5
    try:
        num = int(s)
        return max(1, min(5, num))
    except ValueError:
        return 2

def parse_multi_hazard_tokens(cell_val: Optional[Any]) -> Tuple[int, int, bool]:
    if cell_val is None:
        return 1, 1, False
    s = str(cell_val).strip().upper()
    if not s or s in ("NONE", "NIL", "NO WARNING", "-"):
        return 1, 1, False

    tokens = [t.strip() for t in re.split(r"[,/;\s]+", s) if t.strip()]
    tslg_code = 1
    inten_code = 1
    has_inten = False

    for t in tokens:
        if "TSLG5" in t or "50-60" in t:
            tslg_code = max(tslg_code, 4)
        elif "TSLG4" in t or "40-50" in t:
            tslg_code = max(tslg_code, 3)
        elif "TSLG3" in t or "30-40" in t or "TSLG" in t or "TSLT" in t or "THUNDERSTORM" in t:
            tslg_code = max(tslg_code, 2)

        if "EHR" in t or "EXHVY" in t or "EXTREMELY" in t:
            inten_code = max(inten_code, 4)
            has_inten = True
        elif "VHR" in t or "VHVY" in t or "VERY HEAVY" in t:
            inten_code = max(inten_code, 3)
            has_inten = True
        elif "HR" in t or "IHVY" in t or "HEAVY" in t:
            inten_code = max(inten_code, 2)
            has_inten = True

    return tslg_code, inten_code, has_inten

def parse_thunderstorm_code(val: Optional[Any]) -> int:
    tslg_code, _, _ = parse_multi_hazard_tokens(val)
    return tslg_code

def parse_intensity_code(val: Optional[Any]) -> int:
    _, inten_code, _ = parse_multi_hazard_tokens(val)
    return inten_code

DISTRICT_TEMP_OFFSETS = {
    "Adilabad": 1.5,
    "KomaramBheem": 1.8,
    "Mancherial": 2.1,
    "Nirmal": 1.2,
    "Nizamabad": 1.6,
    "Jagitial": 1.4,
    "RajannaSiricilla": 1.0,
    "Karimnagar": 1.3,
    "Peddapalle": 2.2,
    "JayashankarBhupalapalle": 1.7,
    "Mulugu": 1.1,
    "Bkothagudem": 2.5,
    "Khammam": 1.8,
    "Nalgonda": 1.4,
    "Suryapet": 1.3,
    "Mahabubabad": 1.2,
    "Warangal": 0.8,
    "Hanumakonda": 0.7,
    "Jangaon": 0.5,
    "Siddipet": 0.3,
    "yadadribhuvanagiri": 0.2,
    "Rangareddy": -0.5,
    "Hyderabad": -0.8,
    "MedchalMalkajgiri": -0.4,
    "Vikarabad": -1.8,
    "SangaReddy": -0.9,
    "Medak": -0.2,
    "Kamareddy": 0.2,
    "MahabubNagar": 0.4,
    "NagarKurnool": 0.1,
    "Wanaparthy": 0.3,
    "Narayanpet": -0.3,
    "JogulambaGadwal": 0.8,
}

def _extract_base_temp(val: Optional[Any], default_mid: float = 42.0) -> float:
    if val is None:
        return default_mid
    s = str(val).strip()
    nums = re.findall(r"\d+\.?\d*", s)
    if len(nums) >= 2:
        return round((float(nums[0]) + float(nums[1])) / 2.0, 1)
    elif len(nums) == 1:
        return float(nums[0])
    return default_mid

def parse_multi_hazard_excel_memory(excel_path: str) -> Dict[str, Any]:
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Multi-Hazard Excel file not found: {excel_path}")

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb["7-Day Forecast"] if "7-Day Forecast" in wb.sheetnames else wb.active

    header_row = 2
    for r in range(1, min(6, sheet.max_row + 1)):
        row_vals = [str(sheet.cell(r, c).value or "").strip().lower() for c in range(1, min(15, sheet.max_column + 1))]
        if "district" in row_vals or "day 1 forecast" in row_vals:
            header_row = r
            break

    col_map = {}
    for c in range(1, sheet.max_column + 1):
        val = str(sheet.cell(header_row, c).value or "").strip().lower()
        if not val:
            continue
        if "s.no" in val or "sno" in val:
            col_map["sno"] = c
        elif "sub division" in val or "subdivision" in val:
            col_map["subdiv"] = c
        elif "district" in val:
            col_map["district"] = c
        for d in range(1, 8):
            if f"day {d} forecast" in val or f"day{d} forecast" in val or f"day {d} fcst" in val:
                col_map[f"spatial{d}"] = c
            if f"day {d} warning" in val or f"day{d} warning" in val or f"day {d} wrng" in val:
                col_map[f"warning{d}"] = c

    dist_col = col_map.get("district", 3)
    subdiv_col = col_map.get("subdiv", 2)

    districts_data = []
    summary_row = None
    has_intensity_data = False

    for r in range(header_row + 1, sheet.max_row + 1):
        raw_dist = sheet.cell(r, dist_col).value
        if not raw_dist or str(raw_dist).strip() == "":
            continue

        raw_str = str(raw_dist).strip()
        if raw_str.lower() in ("telangana", "state", "total"):
            summary_row = {
                "District": "Telangana",
                "SubDivision": "Telangana",
            }
            for d in range(1, 8):
                sp_col = col_map.get(f"spatial{d}", 4 + (d - 1) * 2 if d <= 5 else 13 + (d - 5))
                summary_row[f"spatial{d}"] = parse_spatial_code(sheet.cell(r, sp_col).value)
            continue

        std_name, code, lat, lon = match_district_meta(raw_str)
        subdiv = str(sheet.cell(r, subdiv_col).value or "").strip()

        row_dict = {
            "District": std_name,
            "district codes": code,
            "lat": lat,
            "long": lon,
            "subdivision": subdiv,
        }

        for d in range(1, 8):
            sp_col = col_map.get(f"spatial{d}", 4 + (d - 1) * 2 if d <= 5 else 13 + (d - 5))
            row_dict[f"spatial{d}"] = parse_spatial_code(sheet.cell(r, sp_col).value)

        for d in range(1, 6):
            wr_col = col_map.get(f"warning{d}", 5 + (d - 1) * 2)
            val_wrng = sheet.cell(r, wr_col).value
            tslg_code, inten_code, has_inten = parse_multi_hazard_tokens(val_wrng)
            
            row_dict[f"tslg{d}"] = tslg_code
            row_dict[f"warning{d}"] = tslg_code
            row_dict[f"inten{d}"] = inten_code

            if has_inten:
                has_intensity_data = True

        districts_data.append(row_dict)

    wb.close()

    return {
        "file_name": os.path.basename(excel_path),
        "has_intensity_data": has_intensity_data,
        "districts": districts_data,
        "summary_row": summary_row,
    }

def parse_summer_excel_memory(excel_path: str) -> Dict[str, Any]:
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Summer Excel file not found: {excel_path}")

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.active

    day_cols = {
        1: (9, 10, 12),
        2: (14, 15, 16),
        3: (17, 18, 19),
        4: (20, 21, 22),
        5: (23, 24, 25),
    }

    districts_data = []

    for r in range(4, sheet.max_row + 1):
        raw_dist_name = sheet.cell(row=r, column=4).value
        if not raw_dist_name or str(raw_dist_name).strip() == "":
            continue

        std_name, code, lat, lon = match_district_meta(str(raw_dist_name))
        offset = DISTRICT_TEMP_OFFSETS.get(std_name, 0.0)

        row_dict = {
            "District": std_name,
            "district codes": code,
            "lat": lat,
            "long": lon,
        }

        for day in range(1, 6):
            fcst_col, wrng_col, temp_col = day_cols[day]
            val_fcst = sheet.cell(row=r, column=fcst_col).value
            val_wrng = sheet.cell(row=r, column=wrng_col).value
            val_temp = sheet.cell(row=r, column=temp_col).value

            row_dict[f"spatial{day}"] = parse_spatial_code(val_fcst)
            row_dict[f"warning{day}"] = parse_intensity_code(val_wrng)

            base_temp = _extract_base_temp(val_temp, default_mid=41.5)
            day_shift = (day - 1) * 0.4
            tmax_val = round(base_temp + offset + day_shift, 1)
            tmin_val = round(max(20.0, tmax_val - 14.5 + (offset * 0.3)), 1)

            row_dict[f"tmax{day}"] = tmax_val
            row_dict[f"tmin{day}"] = tmin_val

        districts_data.append(row_dict)

    wb.close()

    return {
        "file_name": os.path.basename(excel_path),
        "districts": districts_data,
    }

def parse_any_excel_memory(excel_path: str) -> Dict[str, Any]:
    fname = os.path.basename(excel_path).lower()
    if "summer" in fname:
        return parse_summer_excel_memory(excel_path)
    else:
        return parse_multi_hazard_excel_memory(excel_path)

def parse_rain_excel(excel_path: str, output_csv_dir: str = None) -> Dict[str, Any]:
    return parse_multi_hazard_excel_memory(excel_path)

def parse_summer_excel(excel_path: str, output_csv_dir: str = None) -> Dict[str, Any]:
    return parse_summer_excel_memory(excel_path)

def parse_imd_excel(excel_path: str, output_csv_dir: str = None) -> Dict[str, Any]:
    fname = os.path.basename(excel_path).lower()
    if "summer" in fname:
        return parse_summer_excel_memory(excel_path)
    else:
        return parse_multi_hazard_excel_memory(excel_path)
