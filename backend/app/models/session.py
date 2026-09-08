from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date, time
from app.database import Base

class MonitoringSession(Base):
    __tablename__ = "monitoring_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_name = Column(String(150), nullable=False)
    upt_name = Column(String(100), default="BALMON SFR KELAS I YOGYAKARTA")
    monitoring_station = Column(String(100), default="STASIUN MONITORING SMSN")
    spt_number = Column(String(100), nullable=True)
    officer_name = Column(String(100), nullable=True)
    
    monitoring_date = Column(Date, default=date.today)
    monitoring_time = Column(Time, default=datetime.utcnow().time)
    
    address = Column(String(200), nullable=True)
    district = Column(String(100), nullable=True) # Kecamatan
    city = Column(String(100), nullable=True)     # Kabupaten / Kota
    province = Column(String(100), default="D.I. Yogyakarta")
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    device_type = Column(String(50), default="TCI") # TCI, Argus, LS306, etc.
    raw_filename = Column(String(200), nullable=True)
    
    start_frequency_mhz = Column(Float, nullable=True)
    stop_frequency_mhz = Column(Float, nullable=True)
    threshold_dbuvm = Column(Float, default=50.0)
    detection_radius_km = Column(Float, default=50.0)
    marker_filter = Column(String(50), default="all") # all, peak, offair, blm_diketahui, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="sessions")
    scan_points = relationship("ScanPoint", back_populates="session", cascade="all, delete-orphan")
    identification_results = relationship("IdentificationResult", back_populates="session", cascade="all, delete-orphan")
