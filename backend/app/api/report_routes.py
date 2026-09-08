from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import datetime, date
from collections import Counter

from app.database import get_db
from app.models.session import MonitoringSession
from app.models.identification import IdentificationResult
from app.exporters.rol_excel_exporter import generate_rol_excel
from app.exporters.docx_pdf_exporter import generate_report_docx

router = APIRouter(prefix="/report", tags=["Reports & Exports"])

@router.get("/export-rol/{session_id}")
def export_rol_excel(session_id: int, db: Session = Depends(get_db)):
    sess = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sesi monitoring tidak ditemukan")
        
    recs = db.query(IdentificationResult).filter(IdentificationResult.session_id == session_id).order_by(IdentificationResult.frequency_mhz.asc()).all()
    
    session_data = {
        "session_name": sess.session_name,
        "upt_name": sess.upt_name,
        "monitoring_station": sess.monitoring_station,
        "spt_number": sess.spt_number,
        "officer_name": sess.officer_name,
        "monitoring_date": sess.monitoring_date,
        "latitude": sess.latitude,
        "longitude": sess.longitude,
        "device_type": sess.device_type,
        "threshold_dbuvm": sess.threshold_dbuvm,
        "detection_radius_km": sess.detection_radius_km
    }
    
    results = [
        {
            "frequency_mhz": r.frequency_mhz,
            "level_dbuvm": r.level_dbuvm,
            "is_peak": r.is_peak,
            "identified_name": r.identified_name,
            "status": r.status,
            "distance_km": r.distance_km,
            "station_city": r.station_city,
            "service": r.service,
            "subservice": r.subservice,
            "emission_class": r.emission_class,
            "matched_source": r.matched_source
        }
        for r in recs
    ]
    
    excel_bytes = generate_rol_excel(session_data, results)
    filename = f"ROL_{sess.session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/export-docx/{session_id}")
def export_docx_report(session_id: int, db: Session = Depends(get_db)):
    sess = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sesi monitoring tidak ditemukan")
        
    recs = db.query(IdentificationResult).filter(IdentificationResult.session_id == session_id).order_by(IdentificationResult.frequency_mhz.asc()).all()
    
    session_data = {
        "session_name": sess.session_name,
        "upt_name": sess.upt_name,
        "monitoring_station": sess.monitoring_station,
        "spt_number": sess.spt_number,
        "officer_name": sess.officer_name,
        "monitoring_date": sess.monitoring_date,
        "monitoring_time": sess.monitoring_time,
        "latitude": sess.latitude,
        "longitude": sess.longitude,
        "device_type": sess.device_type,
        "start_frequency_mhz": sess.start_frequency_mhz,
        "stop_frequency_mhz": sess.stop_frequency_mhz,
        "threshold_dbuvm": sess.threshold_dbuvm,
        "detection_radius_km": sess.detection_radius_km
    }
    
    results = [
        {
            "frequency_mhz": r.frequency_mhz,
            "level_dbuvm": r.level_dbuvm,
            "is_peak": r.is_peak,
            "identified_name": r.identified_name,
            "status": r.status,
            "distance_km": r.distance_km,
            "station_city": r.station_city,
            "service": r.service
        }
        for r in recs
    ]
    
    status_summary = dict(Counter(r.status for r in recs if r.status != "Clear"))
    docx_bytes = generate_report_docx(session_data, results, status_summary)
    filename = f"Laporan_{sess.session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"
    
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
