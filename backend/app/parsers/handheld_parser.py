import csv
import io
import re
from datetime import datetime, date, time
from typing import List, Optional
from app.parsers.base import BaseSpectrumParser, UnifiedScanResult, ScanPointData
from app.parsers.argus_parser import parse_dms_to_decimal

class HandheldParser(BaseSpectrumParser):
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        fn = filename.lower()
        if any(k in fn for k in ["anritsu", "agilent", "n9930", "fieldfox", "ms27", "s331", "s332"]):
            return True
        text = file_content[:3000].decode("latin-1", errors="ignore").lower()
        return any(k in text for k in [
            "anritsu", "agilent", "n9930", "fieldfox", "spectrum master",
            "trace a", "trace b", "trace data", "center frequency", "span", "reference level"
        ])

    def parse(self, file_content: bytes, filename: str) -> UnifiedScanResult:
        text = file_content.decode("latin-1", errors="ignore")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        if not lines:
            raise ValueError("File scan handheld kosong")
            
        # Detect delimiter
        delimiter = ","
        sample_text = "\n".join(lines[:20])
        if "\t" in sample_text:
            delimiter = "\t"
        elif ";" in sample_text and sample_text.count(";") > sample_text.count(","):
            delimiter = ";"
            
        device_name = "Anritsu / Agilent N9930B"
        fn_low = filename.lower()
        text_low = text[:2000].lower()
        if "anritsu" in fn_low or "anritsu" in text_low or "ms27" in fn_low or "ms27" in text_low:
            device_name = "Anritsu"
        elif "agilent" in fn_low or "agilent" in text_low or "n9930" in fn_low or "fieldfox" in text_low:
            device_name = "Agilent N9930B"

        latitude = -7.733139
        longitude = 110.471667
        scan_date = date.today()
        scan_time = datetime.now().time()
        
        # 1. Parse Metadata in Header Rows
        data_start_idx = -1
        freq_col_idx = 0
        level_col_idx = 1
        
        for idx, line in enumerate(lines[:600]):
            parts = [p.strip() for p in line.split(delimiter)]
            p_lower = [p.lower() for p in parts]
            joined = " ".join(p_lower)
            
            # Date / Time extraction
            if any(k in joined for k in ["date", "time", "date/time", "timestamp"]):
                for p in parts:
                    for fmt in [
                        "%m/%d/%Y %I:%M:%S %p", "%d/%m/%Y %H:%M:%S",
                        "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S",
                        "%d/%m/%Y", "%Y-%m-%d"
                    ]:
                        try:
                            clean_p = re.sub(r'^[^\d]+', '', p.strip())
                            dt = datetime.strptime(clean_p, fmt)
                            scan_date = dt.date()
                            if hasattr(dt, 'hour') and dt.hour != 0:
                                scan_time = dt.time()
                            break
                        except ValueError:
                            continue
                            
            # GPS Coordinates
            if "latitude" in joined or "lat:" in joined:
                for p in parts:
                    if "lat" in p.lower():
                        val = parse_dms_to_decimal(p.split(":")[-1])
                        if val is not None:
                            latitude = val
            if "longitude" in joined or "lon:" in joined or "long:" in joined:
                for p in parts:
                    if "lon" in p.lower() or "long" in p.lower():
                        val = parse_dms_to_decimal(p.split(":")[-1])
                        if val is not None:
                            longitude = val

            # Check if this line is header of trace data
            if any(k in joined for k in ["frequency", "freq", "freq(hz)", "freq(mhz)", "trace data", "amplitude", "level(dbm)"]):
                for c_idx, col in enumerate(p_lower):
                    if "freq" in col:
                        freq_col_idx = c_idx
                    elif any(l_name in col for l_name in ["amp", "level", "power", "dbm", "dbuv", "trace", "value"]):
                        level_col_idx = c_idx
                data_start_idx = idx + 1
                break
                
            # Or if line has 2+ pure numeric numbers (float, float)
            if data_start_idx == -1 and len(parts) >= 2:
                try:
                    f_val = float(parts[0].replace(",", "."))
                    l_val = float(parts[1].replace(",", "."))
                    if abs(f_val) > 0:
                        data_start_idx = idx
                        break
                except ValueError:
                    pass
                    
        if data_start_idx == -1:
            data_start_idx = 0

        # 2. Parse Points
        points: List[ScanPointData] = []
        is_hz_detected = False
        is_dbm_detected = False
        
        for line in lines[data_start_idx:]:
            parts = [p.strip() for p in line.split(delimiter)]
            if len(parts) <= max(freq_col_idx, level_col_idx):
                continue
            try:
                f_str = parts[freq_col_idx].replace(",", ".")
                l_str = parts[level_col_idx].replace(",", ".")
                if not f_str or not l_str:
                    continue
                raw_freq = float(f_str)
                raw_level = float(l_str)
                
                # Check Hz vs MHz
                if raw_freq > 10000.0:
                    is_hz_detected = True
                    freq_mhz = raw_freq / 1_000_000.0
                else:
                    freq_mhz = raw_freq
                    
                # Check dBm vs dBuV/m
                # In spectrum analyzers (Anritsu / Agilent), power is in dBm (typically <= 0 dBm or negative)
                # Conversion to dBuV/m (50 ohm system) is: dBuV/m = dBm + 107 dB
                if raw_level <= 0 or "dbm" in text_low:
                    is_dbm_detected = True
                    level_dbuvm = raw_level + 107.0
                else:
                    level_dbuvm = raw_level
                    
                points.append(ScanPointData(frequency_mhz=freq_mhz, level_dbuvm=level_dbuvm))
            except (ValueError, IndexError):
                continue
                
        if not points:
            raise ValueError(f"Tidak ada data frekuensi dan level yang valid ditemukan di file {device_name}")
            
        freqs = [p.frequency_mhz for p in points]
        levels = [p.level_dbuvm for p in points]
        
        return UnifiedScanResult(
            device_type=device_name,
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
            metadata={
                "device": device_name,
                "total_points": len(points),
                "is_hz_converted": is_hz_detected,
                "is_dbm_converted_to_dbuvm": is_dbm_detected
            }
        )
