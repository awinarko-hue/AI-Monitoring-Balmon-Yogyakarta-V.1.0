from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class IdentificationResult(Base):
    __tablename__ = "identification_results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("monitoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_point_id = Column(Integer, ForeignKey("scan_points.id", ondelete="CASCADE"), nullable=True)
    
    frequency_mhz = Column(Float, nullable=False, index=True)
    level_dbuvm = Column(Float, nullable=False)
    is_peak = Column(Boolean, default=False)
    
    # Identification info
    identified_name = Column(String(200), default="Belum Teridentifikasi")
    service = Column(String(100), nullable=True)
    subservice = Column(String(100), nullable=True)
    emission_class = Column(String(50), nullable=True)
    
    # Status: Legal | Ilegal | Tidak Sesuai ISR | Kadaluarsa | Belum Diketahui | Off Air | Internasional
    status = Column(String(50), nullable=False, index=True)
    distance_km = Column(Float, nullable=True)
    
    station_latitude = Column(Float, nullable=True)
    station_longitude = Column(Float, nullable=True)
    station_city = Column(String(100), nullable=True)
    
    matched_sims_id = Column(Integer, ForeignKey("sims_records.id", ondelete="SET NULL"), nullable=True)
    matched_manual_id = Column(Integer, ForeignKey("manual_stations.id", ondelete="SET NULL"), nullable=True)
    matched_source = Column(String(20), default="NONE") # "SIMS" | "MANUAL" | "NONE"
    
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("MonitoringSession", back_populates="identification_results")
    matched_sims = relationship("SimsRecord")
    matched_manual = relationship("ManualStation")
