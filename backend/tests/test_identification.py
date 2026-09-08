import pytest
from datetime import date, timedelta
from app.core.identification_engine import IdentificationEngine

def test_identification_legal_status():
    monitoring_lat = -7.733139
    monitoring_lon = 110.471667
    engine = IdentificationEngine(
        monitoring_lat=monitoring_lat,
        monitoring_lon=monitoring_lon,
        monitoring_date=date(2026, 9, 7),
        detection_radius_km=50.0,
        threshold_dbuvm=50.0
    )
    
    sims_records = [
        {
            "id": 1,
            "freq_mhz": 100.2,
            "client_name": "RADIO RETJO BUNTUNG FM",
            "latitude": -7.7956,
            "longitude": 110.3695,
            "service": "PENYIARAN",
            "subservice": "RADIO FM",
            "expiry_date": date(2027, 12, 31) # Valid active license
        }
    ]
    
    scan_points = [
        {"id": 101, "frequency_mhz": 100.0, "level_dbuvm": 30.0},
        {"id": 102, "frequency_mhz": 100.2, "level_dbuvm": 65.0}, # Peak & Match
        {"id": 103, "frequency_mhz": 100.4, "level_dbuvm": 25.0}
    ]
    
    results = engine.process_session(scan_points, sims_records, [])
    
    # 100.2 MHz should be Legal
    match_1002 = next(r for r in results if r["frequency_mhz"] == 100.2)
    assert match_1002["status"] == "Legal"
    assert match_1002["identified_name"] == "RADIO RETJO BUNTUNG FM"
    assert match_1002["is_peak"] is True
    assert match_1002["distance_km"] < 50.0

def test_identification_expired_status():
    engine = IdentificationEngine(
        monitoring_lat=-7.733139,
        monitoring_lon=110.471667,
        monitoring_date=date(2026, 9, 7),
        threshold_dbuvm=50.0
    )
    
    sims_records = [
        {
            "id": 2,
            "freq_mhz": 95.0,
            "client_name": "RADIO EXPIRED FM",
            "latitude": -7.7500,
            "longitude": 110.4000,
            "expiry_date": date(2024, 1, 1) # Expired license
        }
    ]
    
    scan_points = [
        {"id": 201, "frequency_mhz": 94.8, "level_dbuvm": 30.0},
        {"id": 202, "frequency_mhz": 95.0, "level_dbuvm": 62.0},
        {"id": 203, "frequency_mhz": 95.2, "level_dbuvm": 31.0}
    ]
    
    results = engine.process_session(scan_points, sims_records, [])
    match_95 = next(r for r in results if r["frequency_mhz"] == 95.0)
    assert match_95["status"] == "Kadaluarsa"
    assert match_95["identified_name"] == "RADIO EXPIRED FM"

def test_identification_unknown_peak():
    engine = IdentificationEngine(
        monitoring_lat=-7.733139,
        monitoring_lon=110.471667,
        threshold_dbuvm=50.0
    )
    
    # No SIMS or Manual record for 107.7 MHz
    scan_points = [
        {"id": 301, "frequency_mhz": 107.5, "level_dbuvm": 25.0},
        {"id": 302, "frequency_mhz": 107.7, "level_dbuvm": 58.0}, # Peak without license
        {"id": 303, "frequency_mhz": 107.9, "level_dbuvm": 20.0}
    ]
    
    results = engine.process_session(scan_points, [], [])
    match_1077 = next(r for r in results if r["frequency_mhz"] == 107.7)
    assert match_1077["status"] == "Belum Diketahui"
    assert match_1077["identified_name"] == "Belum Teridentifikasi"

def test_identification_off_air():
    engine = IdentificationEngine(
        monitoring_lat=-7.733139,
        monitoring_lon=110.471667,
        threshold_dbuvm=50.0
    )
    
    sims_records = [
        {
            "id": 3,
            "freq_mhz": 99.0,
            "client_name": "RADIO SILENT FM",
            "latitude": -7.7400,
            "longitude": 110.4200,
            "expiry_date": date(2028, 1, 1)
        }
    ]
    
    # Signal is low (< 50 dBuV/m threshold)
    scan_points = [
        {"id": 401, "frequency_mhz": 99.0, "level_dbuvm": 28.0}
    ]
    
    results = engine.process_session(scan_points, sims_records, [])
    match_99 = next(r for r in results if r["frequency_mhz"] == 99.0)
    assert match_99["status"] == "Off Air"
    assert match_99["identified_name"] == "RADIO SILENT FM"
