from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class ScanPoint(Base):
    __tablename__ = "scan_points"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("monitoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    frequency_mhz = Column(Float, nullable=False, index=True)
    level_dbuvm = Column(Float, nullable=False)
    is_peak = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("MonitoringSession", back_populates="scan_points")
