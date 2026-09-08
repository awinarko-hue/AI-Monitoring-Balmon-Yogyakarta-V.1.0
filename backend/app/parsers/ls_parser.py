import csv
import io
from datetime import datetime, date
from typing import List
from app.parsers.base import BaseSpectrumParser, UnifiedScanResult, ScanPointData

class LSParser(BaseSpectrumParser):
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        fn = filename.lower()
        if any(k in fn for k in ["ls306", "ls327", "ls327w", "ls_"]):
            return True
        text = file_content[:2048].decode("latin-1", errors="ignore").lower()
        return "ls306" in text or "ls327" in text or "maxhold vertical" in text

    def parse(self, file_content: bytes, filename: str) -> UnifiedScanResult:
        text = file_content.decode("latin-1", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        
        if not rows:
            raise ValueError("File LS kosong")
            
        header_idx = -1
        freq_col = 0
        level_col = 1
        
        for idx, row in enumerate(rows[:30]):
            for c_idx, cell in enumerate(row):
                c_low = cell.strip().lower()
                if "freq" in c_low:
                    header_idx = idx
                    freq_col = c_idx
                    for l_idx, l_cell in enumerate(row):
                        l_low = l_cell.strip().lower()
                        if any(k in l_low for k in ["level", "field", "dbuv", "dbm", "maxhold"]):
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
                freq = float(f_str)
                level = float(l_str)
                points.append(ScanPointData(frequency_mhz=freq, level_dbuvm=level))
            except (ValueError, IndexError):
                continue
                
        if not points:
            raise ValueError("Tidak ada data titik frekuensi dan level yang valid ditemukan di file LS306/LS327W")
            
        freqs = [p.frequency_mhz for p in points]
        levels = [p.level_dbuvm for p in points]
        
        return UnifiedScanResult(
            device_type="LS306 / LS327W",
            filename=filename,
            latitude=-7.733139,
            longitude=110.471667,
            scan_date=date.today(),
            scan_time=datetime.now().time(),
            points=points,
            min_frequency_mhz=min(freqs),
            max_frequency_mhz=max(freqs),
            min_level_dbuvm=min(levels),
            max_level_dbuvm=max(levels),
            metadata={"device": "LS Series Spectrum Analyzer"}
        )
