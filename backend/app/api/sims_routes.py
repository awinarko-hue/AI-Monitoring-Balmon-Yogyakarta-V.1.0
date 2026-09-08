from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app.models.sims import SimsDataset, SimsRecord
from app.models.manual_station import ManualStation
from app.schemas.sims import SimsDatasetResponse, SimsRecordSchema, ManualStationCreate, ManualStationResponse
from app.parsers.sims_parser import parse_sims_excel
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/sims", tags=["SIMS Database"])

@router.post("/upload", response_model=SimsDatasetResponse)
async def upload_sims_file(
    file: UploadFile = File(...),
    dataset_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File SIMS kosong")
        
    try:
        parsed = parse_sims_excel(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal mem-parsing file SIMS: {str(e)}")
        
    ds_name = dataset_name or f"SIMS_{parsed['query_date'].strftime('%Y%m%d')}_{file.filename}"
    
    # Deactivate previous active datasets if any
    db.query(SimsDataset).update({SimsDataset.is_active: False})
    
    new_dataset = SimsDataset(
        dataset_name=ds_name,
        query_date=parsed["query_date"],
        uploaded_by=current_user.full_name if current_user else "Admin Balmon",
        total_records=parsed["total_records"],
        is_active=True
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    
    # Batch insert records
    record_objs = [
        SimsRecord(
            dataset_id=new_dataset.id,
            freq_mhz=r["freq_mhz"],
            client_name=r["client_name"],
            latitude=r["latitude"],
            longitude=r["longitude"],
            service=r["service"],
            subservice=r["subservice"],
            emission_class=r["emission_class"],
            equipment_type=r["equipment_type"],
            station_name=r["station_name"],
            city=r["city"],
            expiry_date=r["expiry_date"],
            query_date=r["query_date"]
        )
        for r in parsed["records"]
    ]
    db.bulk_save_objects(record_objs)
    db.commit()
    
    return new_dataset

@router.get("/datasets", response_model=List[SimsDatasetResponse])
def get_sims_datasets(db: Session = Depends(get_db)):
    return db.query(SimsDataset).order_by(SimsDataset.uploaded_at.desc()).all()

@router.get("/records", response_model=List[SimsRecordSchema])
def get_sims_records(
    search: Optional[str] = None,
    dataset_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(SimsRecord)
    if dataset_id is not None:
        query = query.filter(SimsRecord.dataset_id == dataset_id)
    else:
        # Default to active dataset
        active_ds = db.query(SimsDataset).filter(SimsDataset.is_active == True).first()
        if active_ds:
            query = query.filter(SimsRecord.dataset_id == active_ds.id)
            
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (SimsRecord.client_name.ilike(search_pattern)) | 
            (SimsRecord.station_name.ilike(search_pattern)) |
            (SimsRecord.service.ilike(search_pattern)) |
            (SimsRecord.city.ilike(search_pattern))
        )
        
    return query.offset(skip).limit(limit).all()

# Manual Station (Tambahan Data SIMS) CRUD
@router.get("/manual-stations", response_model=List[ManualStationResponse])
def get_manual_stations(db: Session = Depends(get_db)):
    return db.query(ManualStation).filter(ManualStation.is_active == True).order_by(ManualStation.freq_mhz.asc()).all()

@router.post("/manual-stations", response_model=ManualStationResponse)
def create_manual_station(
    req: ManualStationCreate, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    stn = ManualStation(
        freq_mhz=req.freq_mhz,
        client_name=req.client_name,
        latitude=req.latitude,
        longitude=req.longitude,
        service=req.service,
        subservice=req.subservice,
        emission_class=req.emission_class,
        status_legality=req.status_legality,
        notes=req.notes,
        is_active=True
    )
    db.add(stn)
    db.commit()
    db.refresh(stn)
    return stn

@router.delete("/manual-stations/{station_id}")
def delete_manual_station(
    station_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    stn = db.query(ManualStation).filter(ManualStation.id == station_id).first()
    if not stn:
        raise HTTPException(status_code=404, detail="Stasiun manual tidak ditemukan")
    db.delete(stn)
    db.commit()
    return {"message": f"Stasiun manual ID {station_id} berhasil dihapus"}
