from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class SimsRecordSchema(BaseModel):
    id: Optional[int] = None
    dataset_id: Optional[int] = None
    freq_mhz: float
    client_name: str
    latitude: float
    longitude: float
    service: Optional[str] = None
    subservice: Optional[str] = None
    emission_class: Optional[str] = None
    equipment_type: Optional[str] = None
    station_name: Optional[str] = None
    city: Optional[str] = None
    expiry_date: Optional[date] = None
    query_date: Optional[date] = None
    
    class Config:
        from_attributes = True

class SimsDatasetResponse(BaseModel):
    id: int
    dataset_name: str
    query_date: Optional[date] = None
    uploaded_by: Optional[str] = None
    total_records: int
    is_active: bool
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class ManualStationCreate(BaseModel):
    freq_mhz: float
    client_name: str
    latitude: float
    longitude: float
    service: Optional[str] = None
    subservice: Optional[str] = None
    emission_class: Optional[str] = None
    status_legality: str = "Legal" # Legal, Ilegal, Tidak Sesuai ISR, Kadaluarsa, Internasional, Off Air, Belum Diketahui
    notes: Optional[str] = None

class ManualStationResponse(ManualStationCreate):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
