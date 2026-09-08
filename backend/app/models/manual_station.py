from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from app.database import Base

class ManualStation(Base):
    __tablename__ = "manual_stations"
    
    id = Column(Integer, primary_key=True, index=True)
    freq_mhz = Column(Float, nullable=False, index=True)
    client_name = Column(String(200), nullable=False) # NAMA PENGGUNA
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    service = Column(String(100), nullable=True)
    subservice = Column(String(100), nullable=True)
    emission_class = Column(String(50), nullable=True)
    
    # Custom status legality: Legal | Ilegal | Tidak Sesuai ISR | Kadaluarsa | Internasional | Off Air | Belum Diketahui
    status_legality = Column(String(50), default="Legal")
    notes = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
