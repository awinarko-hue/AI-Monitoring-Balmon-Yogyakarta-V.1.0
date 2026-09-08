from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import os

from app.database import get_db
from app.models.session import MonitoringSession
from app.models.scan_data import ScanPoint
from app.models.config_setting import ConfigSetting
from app.schemas.scan import SessionResponse, SessionDetailResponse, ScanPointSchema
from app.parsers import parse_spectrum_file
from app.core.geo import is_within_bounding_box, reverse_geocode
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/scan", tags=["Spectrum Scan"])

@router.get("/reverse-geocode")
def get_reverse_geocode(
    latitude: float,
    longitude: float
):
    """
    Reverse geocode latitude and longitude to get District (Kecamatan), City (Kabupaten/Kota), and Province.
    """
    return reverse_geocode(latitude, longitude)

@router.post("/upload", response_model=SessionDetailResponse)
async def upload_scan_file(
    file: UploadFile = File(...),
    session_name: Optional[str] = Form(None),
    device_type: Optional[str] = Form(None),
    spt_number: Optional[str] = Form(None),
    officer_name: Optional[str] = Form(None),
    monitoring_station: Optional[str] = Form("STASIUN MONITORING SMSN"),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    threshold_dbuvm: Optional[float] = Form(50.0),
    detection_radius_km: Optional[float] = Form(50.0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File kosong")
        
    try:
        parsed_result = parse_spectrum_file(content, file.filename, device_hint=device_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal mem-parsing file scan: {str(e)}")
        
    # Determine coordinates
    final_lat = latitude if latitude is not None else parsed_result.latitude
    final_lon = longitude if longitude is not None else parsed_result.longitude
    
    # Check bounding box from config
    cfg = db.query(ConfigSetting).filter(ConfigSetting.setting_key == "default").first()
    lat_min = cfg.lat_min if cfg else -8.213584
    lat_max = cfg.lat_max if cfg else -7.503037
    lon_min = cfg.lon_min if cfg else 109.375246
    lon_max = cfg.lon_max if cfg else 111.321684
    
    is_valid_area = is_within_bounding_box(final_lat, final_lon, lat_min, lat_max, lon_min, lon_max)
    
    # Auto reverse geocode if district or city is not provided
    final_district = district
    final_city = city
    if not final_district or not final_city:
        geo_res = reverse_geocode(final_lat, final_lon)
        final_district = final_district or geo_res.get("district", "Kalasan")
        final_city = final_city or geo_res.get("city", "SLEMAN")
    
    sess_name = session_name or f"Monitoring_{parsed_result.device_type}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    new_session = MonitoringSession(
        user_id=current_user.id if current_user else None,
        session_name=sess_name,
        upt_name="BALMON SFR KELAS I YOGYAKARTA",
        monitoring_station=monitoring_station or "STASIUN MONITORING SMSN",
        spt_number=spt_number or "",
        officer_name=officer_name or (current_user.full_name if current_user else "Petugas Balmon"),
        monitoring_date=parsed_result.scan_date or date.today(),
        monitoring_time=parsed_result.scan_time or datetime.now().time(),
        address=address or "",
        district=final_district or "Kalasan",
        city=final_city or "SLEMAN",
        province="D.I. Yogyakarta",
        latitude=final_lat,
        longitude=final_lon,
        device_type=parsed_result.device_type,
        raw_filename=file.filename,
        start_frequency_mhz=parsed_result.min_frequency_mhz,
        stop_frequency_mhz=parsed_result.max_frequency_mhz,
        threshold_dbuvm=threshold_dbuvm or (cfg.default_threshold_dbuvm if cfg else 50.0),
        detection_radius_km=detection_radius_km or (cfg.default_radius_km if cfg else 50.0),
        marker_filter="all"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    # Batch insert scan points
    scan_point_objects = [
        ScanPoint(
            session_id=new_session.id,
            frequency_mhz=pt.frequency_mhz,
            level_dbuvm=pt.level_dbuvm,
            is_peak=False,
            timestamp=pt.timestamp or datetime.utcnow()
        )
        for pt in parsed_result.points
    ]
    db.bulk_save_objects(scan_point_objects)
    db.commit()
    
    # Fetch points for response
    pts = db.query(ScanPoint).filter(ScanPoint.session_id == new_session.id).order_by(ScanPoint.frequency_mhz.asc()).all()
    
    return SessionDetailResponse(
        id=new_session.id,
        session_name=new_session.session_name,
        upt_name=new_session.upt_name,
        monitoring_station=new_session.monitoring_station,
        spt_number=new_session.spt_number,
        officer_name=new_session.officer_name,
        monitoring_date=new_session.monitoring_date,
        address=new_session.address,
        district=new_session.district,
        city=new_session.city,
        province=new_session.province,
        latitude=new_session.latitude,
        longitude=new_session.longitude,
        device_type=new_session.device_type,
        raw_filename=new_session.raw_filename,
        start_frequency_mhz=new_session.start_frequency_mhz,
        stop_frequency_mhz=new_session.stop_frequency_mhz,
        threshold_dbuvm=new_session.threshold_dbuvm,
        detection_radius_km=new_session.detection_radius_km,
        marker_filter=new_session.marker_filter,
        created_at=new_session.created_at,
        total_points=len(pts),
        total_peaks=0,
        points=[ScanPointSchema.from_orm(p) for p in pts]
    )

@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(
    skip: int = 0, 
    limit: int = 50, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    sessions = db.query(MonitoringSession).order_by(MonitoringSession.created_at.desc()).offset(skip).limit(limit).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(
    session_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    sess = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sesi monitoring tidak ditemukan")
        
    pts = db.query(ScanPoint).filter(ScanPoint.session_id == session_id).order_by(ScanPoint.frequency_mhz.asc()).all()
    peak_count = db.query(ScanPoint).filter(ScanPoint.session_id == session_id, ScanPoint.is_peak == True).count()
    
    return SessionDetailResponse(
        id=sess.id,
        session_name=sess.session_name,
        upt_name=sess.upt_name,
        monitoring_station=sess.monitoring_station,
        spt_number=sess.spt_number,
        officer_name=sess.officer_name,
        monitoring_date=sess.monitoring_date,
        address=sess.address,
        district=sess.district,
        city=sess.city,
        province=sess.province,
        latitude=sess.latitude,
        longitude=sess.longitude,
        device_type=sess.device_type,
        raw_filename=sess.raw_filename,
        start_frequency_mhz=sess.start_frequency_mhz,
        stop_frequency_mhz=sess.stop_frequency_mhz,
        threshold_dbuvm=sess.threshold_dbuvm,
        detection_radius_km=sess.detection_radius_km,
        marker_filter=sess.marker_filter,
        created_at=sess.created_at,
        total_points=len(pts),
        total_peaks=peak_count,
        points=[ScanPointSchema.from_orm(p) for p in pts]
    )

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    sess = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sesi monitoring tidak ditemukan")
    db.delete(sess)
    db.commit()
    return {"message": f"Sesi ID {session_id} berhasil dihapus"}

@router.post("/sessions/{session_id}/auto-geocode", response_model=SessionResponse)
def auto_geocode_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    sess = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sesi monitoring tidak ditemukan")
    
    geo_res = reverse_geocode(sess.latitude, sess.longitude)
    sess.district = geo_res.get("district", sess.district)
    sess.city = geo_res.get("city", sess.city)
    sess.province = geo_res.get("province", sess.province)
    db.commit()
    db.refresh(sess)
    return SessionResponse(
        id=sess.id,
        session_name=sess.session_name,
        upt_name=sess.upt_name,
        monitoring_station=sess.monitoring_station,
        spt_number=sess.spt_number,
        officer_name=sess.officer_name,
        monitoring_date=sess.monitoring_date,
        address=sess.address,
        district=sess.district,
        city=sess.city,
        province=sess.province,
        latitude=sess.latitude,
        longitude=sess.longitude,
        device_type=sess.device_type,
        raw_filename=sess.raw_filename,
        start_frequency_mhz=sess.start_frequency_mhz,
        stop_frequency_mhz=sess.stop_frequency_mhz,
        threshold_dbuvm=sess.threshold_dbuvm,
        detection_radius_km=sess.detection_radius_km,
        marker_filter=sess.marker_filter,
        created_at=sess.created_at
    )
