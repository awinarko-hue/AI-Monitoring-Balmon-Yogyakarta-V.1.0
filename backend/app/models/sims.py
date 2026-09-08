from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base

class SimsDataset(Base):
    __tablename__ = "sims_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String(150), nullable=False)
    query_date = Column(Date, default=date.today)
    uploaded_by = Column(String(100), nullable=True)
    total_records = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    records = relationship("SimsRecord", back_populates="dataset", cascade="all, delete-orphan")

class SimsRecord(Base):
    __tablename__ = "sims_records"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("sims_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    freq_mhz = Column(Float, nullable=False, index=True)
    client_name = Column(String(200), nullable=False) # CLNT_NAME
    latitude = Column(Float, nullable=False)          # SID_LAT
    longitude = Column(Float, nullable=False)         # SID_LONG
    
    service = Column(String(100), nullable=True)      # SERVICE
    subservice = Column(String(100), nullable=True)   # SUBSERVICE
    emission_class = Column(String(50), nullable=True)# EMIS_CLASS_1
    equipment_type = Column(String(100), nullable=True)# EQUIP_TYPE
    station_name = Column(String(150), nullable=True) # STN_NAME
    city = Column(String(100), nullable=True)         # CITY
    
    expiry_date = Column(Date, nullable=True)         # MASA_LAKU
    query_date = Column(Date, nullable=True)          # TGL_QUERY
    
    dataset = relationship("SimsDataset", back_populates="records")
