from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class IdentificationItemSchema(BaseModel):
    id: Optional[int] = None
    session_id: Optional[int] = None
    scan_point_id: Optional[int] = None
    frequency_mhz: float
    level_dbuvm: float
    is_peak: bool = False
    identified_name: str
    service: Optional[str] = None
    subservice: Optional[str] = None
    emission_class: Optional[str] = None
    status: str
    distance_km: Optional[float] = None
    station_latitude: Optional[float] = None
    station_longitude: Optional[float] = None
    station_city: Optional[str] = None
    matched_source: str = "NONE"
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class IdentificationRunRequest(BaseModel):
    session_id: int
    start_frequency_mhz: Optional[float] = None
    stop_frequency_mhz: Optional[float] = None
    threshold_dbuvm: Optional[float] = 50.0
    detection_radius_km: Optional[float] = 50.0
    marker_filter: Optional[str] = "all"
    preset_id: Optional[int] = None

class IdentificationSummaryResponse(BaseModel):
    session_id: int
    session_name: str
    total_signals: int
    total_peaks: int
    marker_mode: str
    status_breakdown: Dict[str, int]
    results: List[IdentificationItemSchema]
