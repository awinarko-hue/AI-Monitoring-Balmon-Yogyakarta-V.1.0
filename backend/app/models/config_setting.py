from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from datetime import datetime
from app.database import Base

class ConfigSetting(Base):
    __tablename__ = "config_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(50), unique=True, default="default")
    lat_min = Column(Float, default=-8.213584)
    lat_max = Column(Float, default=-7.503037)
    lon_min = Column(Float, default=109.375246)
    lon_max = Column(Float, default=111.321684)
    default_threshold_dbuvm = Column(Float, default=50.0)
    default_radius_km = Column(Float, default=50.0)
    extra_params = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
