from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time, datetime

class ScanPointSchema(BaseModel):
    id: Optional[int] = None
    frequency_mhz: float
    level_dbuvm: float
    is_peak: bool = False
    timestamp: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    session_name: str
    upt_name: Optional[str] = "BALMON SFR KELAS I YOGYAKARTA"
    monitoring_station: Optional[str] = "STASIUN MONITORING SMSN"
    spt_number: Optional[str] = None
    officer_name: Optional[str] = None
    monitoring_date: Optional[date] = None
    address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = "D.I. Yogyakarta"
    latitude: float
    longitude: float
    device_type: Optional[str] = "TCI"
    start_frequency_mhz: Optional[float] = None
    stop_frequency_mhz: Optional[float] = None
    threshold_dbuvm: Optional[float] = 50.0
    detection_radius_km: Optional[float] = 50.0

class SessionResponse(BaseModel):
    id: int
    session_name: str
    upt_name: str
    monitoring_station: str
    spt_number: Optional[str] = None
    officer_name: Optional[str] = None
    monitoring_date: Optional[date] = None
    address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    province: str
    latitude: float
    longitude: float
    device_type: str
    raw_filename: Optional[str] = None
    start_frequency_mhz: Optional[float] = None
    stop_frequency_mhz: Optional[float] = None
    threshold_dbuvm: float
    detection_radius_km: float
    marker_filter: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SessionDetailResponse(SessionResponse):
    total_points: int = 0
    total_peaks: int = 0
    points: List[ScanPointSchema] = []
