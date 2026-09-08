import csv
import io
import re
from datetime import datetime, date, time
from typing import List, Optional, Tuple
import openpyxl
from app.parsers.base import BaseSpectrumParser, UnifiedScanResult, ScanPointData

def parse_dms_to_decimal(dms_str: str) -> Optional[float]:
    """
    Parse DMS coordinate string like:
    - 07°44'00.5"S or 7 44 00.5 S
    - 110°28'17.4"E or 110 28 17.4 E
    - -7.733139 or 110.471667 (already decimal)
    """
    if not dms_str or not isinstance(dms_str, str):
        return None
        
    cleaned = dms_str.strip().replace(",", ".")
    try:
        # Check if already decimal float
        return float(cleaned)
    except ValueError:
        pass
        
    # Match patterns like 07°44'00.5"S or 7°44'0.5" S or 7 44 0.5 S
    match = re.search(r'([0-9]+)[\s°:d]+([0-9]+)[\s\':m]+([0-9]+(?:\.[0-9]+)?)[\s"\'s]*([NSEWnsew])?', cleaned)
    if match:
        deg = float(match.group(1))
        minute = float(match.group(2))
        sec = float(match.group(3))
        direction = match.group(4)
        
        dec = deg + (minute / 60.0) + (sec / 3600.0)
        if direction and direction.upper() in ['S', 'W']:
            dec = -dec
        elif 'S' in cleaned.upper() or 'W' in cleaned.upper():
            dec = -dec
        return dec
        
    return None

class ArgusParser(BaseSpectrumParser):
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        fn = filename.lower()
        if fn.endswith((".csv", ".txt")):
            text = file_content[:2048].decode("latin-1", errors="ignore").lower()
            return "argus" in text or ("frequency [hz]" in text or "freq(hz)" in text or "frequency (hz)" in text)
        elif fn.endswith((".xlsx", ".xls")):
            return "argus" in fn
        return False

    def parse(self, file_content: bytes, filename: str) -> UnifiedScanResult:
        fn = filename.lower()
        rows = []
        
        if fn.endswith((".xlsx", ".xls")):
            wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
            ws = wb.active
            rows = [[str(cell) if cell is not None else "" for cell in row] for row in ws.iter_rows(values_only=True)]
        else:
            text = file_content.decode("latin-1", errors="ignore")
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
            
        if not rows:
            raise ValueError("File Argus kosong")
            
        # Find header
        header_idx = -1
        freq_col = 0
        level_col = 1
        is_hz = True
        
        latitude = -7.733139
        longitude = 110.471667
        scan_date = date.today()
        scan_time = datetime.now().time()
        
        for idx, row in enumerate(rows[:35]):
            row_str = " ".join(row).lower()
            if "latitude" in row_str or "lat:" in row_str or "pos:" in row_str:
                for cell in row:
                    if "lat" in cell.lower():
                        val = parse_dms_to_decimal(cell.split(":")[-1])
                        if val is not None:
                            latitude = val
                    if "lon" in cell.lower() or "long" in cell.lower():
                        val = parse_dms_to_decimal(cell.split(":")[-1])
                        if val is not None:
                            longitude = val
                            
            for c_idx, cell in enumerate(row):
                c_low = cell.strip().lower()
                if "freq" in c_low:
                    header_idx = idx
                    freq_col = c_idx
                    if "mhz" in c_low:
                        is_hz = False
                    for l_idx, l_cell in enumerate(row):
                        l_low = l_cell.strip().lower()
                        if any(k in l_low for k in ["level", "field", "dbuv", "dbm", "strength", "max"]):
                            level_col = l_idx
                            break
                    break
            if header_idx != -1:
                break
                
        if header_idx == -1:
            header_idx = 0
            
        points: List[ScanPointData] = []
        for r_idx in range(header_idx + 1, len(rows)):
            row = rows[r_idx]
            if len(row) <= max(freq_col, level_col):
                continue
            try:
                f_str = row[freq_col].strip().replace(",", ".")
                l_str = row[level_col].strip().replace(",", ".")
                if not f_str or not l_str:
                    continue
                raw_freq = float(f_str)
                freq_mhz = (raw_freq / 1_000_000.0) if (is_hz and raw_freq > 5000) else raw_freq
                level = float(l_str)
                points.append(ScanPointData(frequency_mhz=freq_mhz, level_dbuvm=level))
            except (ValueError, IndexError):
                continue
                
        if not points:
            raise ValueError("Tidak ada data titik frekuensi dan level yang valid ditemukan di file Argus")
            
        freqs = [p.frequency_mhz for p in points]
        levels = [p.level_dbuvm for p in points]
        
        return UnifiedScanResult(
            device_type="Argus",
            filename=filename,
            latitude=latitude,
            longitude=longitude,
            scan_date=scan_date,
            scan_time=scan_time,
            points=points,
            min_frequency_mhz=min(freqs),
            max_frequency_mhz=max(freqs),
            min_level_dbuvm=min(levels),
            max_level_dbuvm=max(levels),
            metadata={"source": "Argus 5/6 Parser", "is_hz_converted": is_hz}
        )
