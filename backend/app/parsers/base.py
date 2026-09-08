from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, date, time

@dataclass
class ScanPointData:
    frequency_mhz: float
    level_dbuvm: float
    timestamp: Optional[datetime] = None

@dataclass
class UnifiedScanResult:
    device_type: str
    filename: str
    latitude: float
    longitude: float
    scan_date: Optional[date]
    scan_time: Optional[time]
    points: List[ScanPointData]
    min_frequency_mhz: float
    max_frequency_mhz: float
    min_level_dbuvm: float
    max_level_dbuvm: float
    metadata: Dict[str, Any]

class BaseSpectrumParser(ABC):
    @abstractmethod
    def parse(self, file_content: bytes, filename: str) -> UnifiedScanResult:
        """
        Parse raw byte content into UnifiedScanResult.
        """
        pass
        
    @abstractmethod
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """
        Inspect header/structure to determine if this parser handles the file.
        """
        pass
