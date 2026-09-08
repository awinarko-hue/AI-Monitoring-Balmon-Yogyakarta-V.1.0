import io
import re
from datetime import datetime, date, time
from typing import List, Optional, Tuple, Dict, Any
from app.parsers.base import BaseSpectrumParser, UnifiedScanResult, ScanPointData

class TCIParser(BaseSpectrumParser):
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        text = file_content[:3000].decode("latin-1", errors="ignore").lower()
        if "sep=^" in text or "channel no." in text or "channel no^" in text:
            return True
        if "maximum field strength" in text and "frequency" in text:
            return True
        if "location (lat)" in text and "location (lon)" in text:
            return True
        return False

    def parse(self, file_content: bytes, filename: str) -> UnifiedScanResult:
        text = file_content.decode("latin-1", errors="ignore")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        if not lines:
            raise ValueError("File TCI kosong")
            
        # Detect delimiter
        delimiter = "^"
        first_line = lines[0]
        if first_line.startswith("sep="):
            delimiter = first_line.split("=")[1].strip()
            lines = lines[1:] # Skip sep= line
        elif "^" in lines[0] or (len(lines) > 1 and "^" in lines[1]):
            delimiter = "^"
        elif ";" in lines[0] or (len(lines) > 1 and ";" in lines[1]):
            delimiter = ";"
        elif "\t" in lines[0] or (len(lines) > 1 and "\t" in lines[1]):
            delimiter = "\t"
        else:
            delimiter = ","
            
        # Default metadata
        latitude = -7.733139
        longitude = 110.471667
        scan_date: Optional[date] = date.today()
        scan_time: Optional[time] = datetime.now().time()
        station_name = "Kalasan"
        
        # 1. Parse Metadata Header Section
        for idx, line in enumerate(lines[:15]):
            parts = [p.strip() for p in line.split(delimiter)]
            parts_lower = [p.lower() for p in parts]
            
            if "location (lat)" in parts_lower or "station name" in parts_lower or "task id" in parts_lower:
                if idx + 1 < len(lines):
                    val_parts = [v.strip() for v in lines[idx + 1].split(delimiter)]
                    header_map = {name: val_idx for val_idx, name in enumerate(parts_lower)}
                    
                    # Lat / Lon
                    lat_col = header_map.get("location (lat)") or header_map.get("latitude")
                    if lat_col is not None and lat_col < len(val_parts):
                        try:
                            lat_v = float(val_parts[lat_col].replace(",", "."))
                            if abs(lat_v) > 0.01:
                                latitude = lat_v
                        except ValueError:
                            pass
                            
                    lon_col = header_map.get("location (lon)") or header_map.get("longitude")
                    if lon_col is not None and lon_col < len(val_parts):
                        try:
                            lon_v = float(val_parts[lon_col].replace(",", "."))
                            if abs(lon_v) > 0.01:
                                longitude = lon_v
                        except ValueError:
                            pass
                            
                    # Station Name
                    stn_col = header_map.get("station name")
                    if stn_col is not None and stn_col < len(val_parts) and val_parts[stn_col]:
                        station_name = val_parts[stn_col]
                        
                    # Start Time
                    time_col = header_map.get("start time") or header_map.get("date") or header_map.get("time")
                    if time_col is not None and time_col < len(val_parts) and val_parts[time_col]:
                        t_str = val_parts[time_col]
                        for fmt in [
                            "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S",
                            "%d/%m/%Y %I:%M:%S %p", "%d/%m/%Y %H:%M:%S",
                            "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S"
                        ]:
                            try:
                                dt = datetime.strptime(t_str, fmt)
                                scan_date = dt.date()
                                scan_time = dt.time()
                                break
                            except ValueError:
                                continue
                break
                
        # 2. Find Channel Scan Data Table
        data_header_idx = -1
        freq_col_idx = 1
        level_col_idx = 2
        
        for idx, line in enumerate(lines):
            parts = [p.strip() for p in line.split(delimiter)]
            parts_lower = [p.lower() for p in parts]
            
            if any("frequency" in p for p in parts_lower) and any("field strength" in p or "level" in p or "strength" in p for p in parts_lower):
                data_header_idx = idx
                max_col = -1
                avg_col = -1
                for c_idx, col in enumerate(parts_lower):
                    if "frequency" in col:
                        freq_col_idx = c_idx
                    elif "maximum field strength" in col or "max field strength" in col:
                        max_col = c_idx
                    elif "average field strength" in col or "avg field strength" in col:
                        avg_col = c_idx
                    elif "field strength" in col or "level" in col:
                        if max_col == -1:
                            max_col = c_idx
                            
                level_col_idx = max_col if max_col != -1 else (avg_col if avg_col != -1 else 2)
                break
                
        if data_header_idx == -1:
            raise ValueError("Tabel data spektrum ('Frequency' / 'Field Strength') tidak ditemukan dalam file TCI")
            
        # 3. Parse Scan Points
        points: List[ScanPointData] = []
        for line in lines[data_header_idx + 1:]:
            parts = [p.strip() for p in line.split(delimiter)]
            if len(parts) <= max(freq_col_idx, level_col_idx):
                continue
            try:
                f_str = parts[freq_col_idx].replace(",", ".")
                l_str = parts[level_col_idx].replace(",", ".")
                if not f_str or not l_str:
                    continue
                freq = float(f_str)
                level = float(l_str)
                points.append(ScanPointData(frequency_mhz=freq, level_dbuvm=level))
            except (ValueError, IndexError):
                continue
                
        if not points:
            raise ValueError("Tidak ada data titik frekuensi dan level yang berhasil di-parse dari file TCI")
            
        freqs = [p.frequency_mhz for p in points]
        levels = [p.level_dbuvm for p in points]
        
        return UnifiedScanResult(
            device_type="TCI",
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
                "station_name": station_name,
                "total_points": len(points),
                "delimiter": delimiter
            }
        )
