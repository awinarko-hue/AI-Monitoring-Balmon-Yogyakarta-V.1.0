from typing import Optional
from app.parsers.base import BaseSpectrumParser, UnifiedScanResult, ScanPointData
from app.parsers.tci_parser import TCIParser
from app.parsers.argus_parser import ArgusParser
from app.parsers.ls_parser import LSParser
from app.parsers.handheld_parser import HandheldParser

PARSERS = [
    TCIParser(),
    ArgusParser(),
    LSParser(),
    HandheldParser(),
]

def parse_spectrum_file(
    file_content: bytes, 
    filename: str, 
    device_hint: Optional[str] = None
) -> UnifiedScanResult:
    """
    Auto-detect and parse spectrum analyzer scan file into UnifiedScanResult.
    """
    # 1. Try explicit hint if provided
    if device_hint:
        hint_low = device_hint.lower()
        if "tci" in hint_low:
            return TCIParser().parse(file_content, filename)
        elif "argus" in hint_low:
            return ArgusParser().parse(file_content, filename)
        elif "ls" in hint_low:
            return LSParser().parse(file_content, filename)
        elif "anritsu" in hint_low or "agilent" in hint_low:
            return HandheldParser().parse(file_content, filename)
            
    # 2. Try auto-detect based on parser.can_parse
    for p in PARSERS:
        if p.can_parse(file_content, filename):
            try:
                return p.parse(file_content, filename)
            except Exception:
                continue
                
    # 3. Fallback: try TCI then Argus then LS then Handheld
    for p in PARSERS:
        try:
            return p.parse(file_content, filename)
        except Exception:
            continue
            
    raise ValueError(f"Format file scan '{filename}' tidak dikenali oleh parser yang tersedia (TCI, Argus 5/6, LS306, LS327W, Anritsu, Agilent).")
