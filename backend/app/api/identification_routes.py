from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from collections import Counter

from app.database import get_db
from app.models.session import MonitoringSession
from app.models.scan_data import ScanPoint
from app.models.sims import SimsDataset, SimsRecord
from app.models.manual_station import ManualStation
from app.models.identification import IdentificationResult
from app.schemas.identification import IdentificationRunRequest, IdentificationSummaryResponse, IdentificationItemSchema
from app.core.identification_engine import IdentificationEngine
from app.core.presets import FREQUENCY_BAND_PRESETS, get_preset_by_id
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/identification", tags=["Auto Identification Engine"])

@router.get("/presets")
def get_presets():
    return FREQUENCY_BAND_PRESETS

@router.post("/run", response_model=IdentificationSummaryResponse)
def run_auto_identification(
    req: IdentificationRunRequest, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    sess = db.query(MonitoringSession).filter(MonitoringSession.id == req.session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sesi monitoring tidak ditemukan")
        
    # Determine frequency range
    start_freq = req.start_frequency_mhz
    stop_freq = req.stop_frequency_mhz
    if req.preset_id:
        preset = get_preset_by_id(req.preset_id)
        if preset:
            start_freq = preset["start_freq_mhz"]
            stop_freq = preset["stop_freq_mhz"]
            
    # Update session parameters
    sess.start_frequency_mhz = start_freq
    sess.stop_frequency_mhz = stop_freq
    if req.threshold_dbuvm is not None:
        sess.threshold_dbuvm = req.threshold_dbuvm
    if req.detection_radius_km is not None:
        sess.detection_radius_km = req.detection_radius_km
    if req.marker_filter:
        sess.marker_filter = req.marker_filter
    db.commit()
    
    # Load scan points within range (with margin for peak context)
    q = db.query(ScanPoint.id, ScanPoint.frequency_mhz, ScanPoint.level_dbuvm).filter(ScanPoint.session_id == req.session_id)
    if start_freq is not None and stop_freq is not None:
        q = q.filter(ScanPoint.frequency_mhz.between(start_freq - 1.0, stop_freq + 1.0))
    scan_points_tuples = q.order_by(ScanPoint.frequency_mhz.asc()).all()
    
    if not scan_points_tuples:
        scan_points_tuples = db.query(ScanPoint.id, ScanPoint.frequency_mhz, ScanPoint.level_dbuvm).filter(ScanPoint.session_id == req.session_id).order_by(ScanPoint.frequency_mhz.asc()).all()
        
    if not scan_points_tuples:
        raise HTTPException(status_code=400, detail="Tidak ada data scan points dalam sesi ini")
        
    # Load active SIMS dataset
    active_ds = db.query(SimsDataset).filter(SimsDataset.is_active == True).first()
    sims_records = []
    if active_ds:
        sims_recs_db = db.query(SimsRecord).filter(SimsRecord.dataset_id == active_ds.id).all()
        sims_records = [
            {
                "id": r.id,
                "freq_mhz": r.freq_mhz,
                "client_name": r.client_name,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "service": r.service,
                "subservice": r.subservice,
                "emission_class": r.emission_class,
                "city": r.city,
                "expiry_date": r.expiry_date
            }
            for r in sims_recs_db
        ]
        
    # Load manual stations
    manual_recs_db = db.query(ManualStation).filter(ManualStation.is_active == True).all()
    manual_records = [
        {
            "id": m.id,
            "freq_mhz": m.freq_mhz,
            "client_name": m.client_name,
            "latitude": m.latitude,
            "longitude": m.longitude,
            "service": m.service,
            "subservice": m.subservice,
            "emission_class": m.emission_class,
            "status_legality": m.status_legality
        }
        for m in manual_recs_db
    ]
    
    # Run Identification Engine
    engine = IdentificationEngine(
        monitoring_lat=sess.latitude,
        monitoring_lon=sess.longitude,
        monitoring_date=sess.monitoring_date or date.today(),
        detection_radius_km=sess.detection_radius_km,
        threshold_dbuvm=sess.threshold_dbuvm
    )
    
    pt_dicts = [
        {"id": p[0], "frequency_mhz": p[1], "level_dbuvm": p[2]}
        for p in scan_points_tuples
    ]
    
    processed_results = engine.process_session(
        scan_points=pt_dicts,
        sims_records=sims_records,
        manual_stations=manual_records,
        start_freq_mhz=start_freq,
        stop_freq_mhz=stop_freq
    )
    
    # Clear old results for this session
    db.query(IdentificationResult).filter(IdentificationResult.session_id == req.session_id).delete()
    
    # Filter actionable results to persist
    save_results = [r for r in processed_results if r["status"] != "Clear" or r["is_peak"]]
    
    # Save identification results
    id_objs = [
        IdentificationResult(
            session_id=sess.id,
            scan_point_id=r["scan_point_id"],
            frequency_mhz=r["frequency_mhz"],
            level_dbuvm=r["level_dbuvm"],
            is_peak=r["is_peak"],
            identified_name=r["identified_name"],
            service=r.get("service"),
            subservice=r.get("subservice"),
            emission_class=r.get("emission_class"),
            status=r["status"],
            distance_km=r.get("distance_km"),
            station_latitude=r.get("station_latitude"),
            station_longitude=r.get("station_longitude"),
            station_city=r.get("station_city"),
            matched_sims_id=r.get("matched_sims_id"),
            matched_manual_id=r.get("matched_manual_id"),
            matched_source=r.get("matched_source", "NONE")
        )
        for r in save_results
    ]
    if id_objs:
        db.bulk_save_objects(id_objs)
    db.commit()
    
    # Apply marker filter
    filtered_results = engine.filter_marker_results(processed_results, marker_mode=sess.marker_filter)
    
    # Status Breakdown
    status_counts = Counter(r["status"] for r in processed_results if r["status"] != "Clear")
    peak_count = sum(1 for r in processed_results if r["is_peak"])
    
    return IdentificationSummaryResponse(
        session_id=sess.id,
        session_name=sess.session_name,
        total_signals=len(processed_results),
        total_peaks=peak_count,
        marker_mode=sess.marker_filter or "all",
        status_breakdown=dict(status_counts),
        results=[IdentificationItemSchema(**r) for r in filtered_results]
    )

@router.get("/results/{session_id}", response_model=IdentificationSummaryResponse)
def get_identification_results(
    session_id: int, 
    marker_mode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    sess = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sesi monitoring tidak ditemukan")
        
    mode = marker_mode or sess.marker_filter or "all"
    
    recs = db.query(IdentificationResult).filter(IdentificationResult.session_id == session_id).order_by(IdentificationResult.frequency_mhz.asc()).all()
    
    engine = IdentificationEngine(
        monitoring_lat=sess.latitude,
        monitoring_lon=sess.longitude,
        monitoring_date=sess.monitoring_date or date.today(),
        detection_radius_km=sess.detection_radius_km,
        threshold_dbuvm=sess.threshold_dbuvm
    )
    
    rec_dicts = [
        {
            "id": r.id,
            "session_id": r.session_id,
            "scan_point_id": r.scan_point_id,
            "frequency_mhz": r.frequency_mhz,
            "level_dbuvm": r.level_dbuvm,
            "is_peak": r.is_peak,
            "identified_name": r.identified_name,
            "service": r.service,
            "subservice": r.subservice,
            "emission_class": r.emission_class,
            "status": r.status,
            "distance_km": r.distance_km,
            "station_latitude": r.station_latitude,
            "station_longitude": r.station_longitude,
            "station_city": r.station_city,
            "matched_source": r.matched_source,
            "notes": r.notes
        }
        for r in recs
    ]
    
    filtered = engine.filter_marker_results(rec_dicts, marker_mode=mode)
    status_counts = Counter(r["status"] for r in rec_dicts if r["status"] != "Clear")
    peak_count = sum(1 for r in rec_dicts if r["is_peak"])
    
    return IdentificationSummaryResponse(
        session_id=sess.id,
        session_name=sess.session_name,
        total_signals=len(recs),
        total_peaks=peak_count,
        marker_mode=mode,
        status_breakdown=dict(status_counts),
        results=[IdentificationItemSchema(**r) for r in filtered]
    )
