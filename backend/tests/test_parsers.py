import pytest
from app.parsers.tci_parser import TCIParser
from app.parsers.handheld_parser import HandheldParser
from app.parsers.argus_parser import ArgusParser, parse_dms_to_decimal

def test_parse_dms():
    lat = parse_dms_to_decimal("07°44'00.5\"S")
    assert lat is not None
    assert -7.74 < lat < -7.73
    
    lon = parse_dms_to_decimal("110°28'17.4\"E")
    assert lon is not None
    assert 110.47 < lon < 110.48

def test_real_tci_file_parsing():
    parser = TCIParser()
    with open('tests/sample_tci.csv', 'rb') as f:
        content = f.read()

    assert parser.can_parse(content, "Contoh_TCI_SAMPLE.csv") is True
    res = parser.parse(content, "Contoh_TCI_SAMPLE.csv")

    assert res.device_type == "TCI"
    assert res.metadata["station_name"] == "Kalasan"
    assert res.latitude == -7.733139
    assert res.longitude == 110.471667
    assert res.scan_date.year == 2026
    assert res.scan_date.month == 1
    assert res.scan_date.day == 1
    
    # Points verification
    assert len(res.points) == 183
    assert res.points[0].frequency_mhz == 87.0
    assert res.points[0].level_dbuvm == 36.0 # Max Field Strength column
    assert res.points[6].frequency_mhz == 87.3
    assert res.points[6].level_dbuvm == 82.0

def test_anritsu_file_parsing():
    parser = HandheldParser()
    anritsu_sample = b"""# Anritsu Spectrum Master MS2712E
Date/Time, 07/09/2026 09:30:00
GPS Latitude, -7.733139
GPS Longitude, 110.471667
Span, 20.000000, MHz
Reference Level, 0.0, dBm

Frequency (MHz), Amplitude (dBm)
88.0, -71.0
88.2, -35.0
88.4, -65.0
88.6, -72.0
"""
    assert parser.can_parse(anritsu_sample, "Contoh_anritsu.csv") is True
    res = parser.parse(anritsu_sample, "Contoh_anritsu.csv")

    assert res.device_type == "Anritsu"
    assert res.latitude == -7.733139
    assert res.longitude == 110.471667
    assert len(res.points) == 4
    
    # Verify dBm + 107 = dBuV/m
    # 88.0 MHz: -71 dBm + 107 = 36 dBuV/m
    assert res.points[0].frequency_mhz == 88.0
    assert res.points[0].level_dbuvm == 36.0
    # 88.2 MHz: -35 dBm + 107 = 72 dBuV/m
    assert res.points[1].frequency_mhz == 88.2
    assert res.points[1].level_dbuvm == 72.0
