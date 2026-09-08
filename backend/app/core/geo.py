import math
from typing import Tuple

EARTH_RADIUS_KM = 6371.0

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    Uses standard spherical haversine formula matching Balmon VBA calculation.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
        
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    
    # Clip a to [0.0, 1.0] to prevent domain errors
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return EARTH_RADIUS_KM * c

def is_within_bounding_box(lat: float, lon: float, lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> bool:
    """
    Validate if a given coordinate (lat, lon) falls inside the bounding box.
    """
    actual_lat_min = min(lat_min, lat_max)
    actual_lat_max = max(lat_min, lat_max)
    actual_lon_min = min(lon_min, lon_max)
    actual_lon_max = max(lon_min, lon_max)
    
    return (actual_lat_min <= lat <= actual_lat_max) and (actual_lon_min <= lon <= actual_lon_max)

def reverse_geocode(lat: float, lon: float) -> dict:
    """
    Reverse geocode coordinates to extract District (Kecamatan) and City/Regency (Kabupaten/Kota).
    Includes preset detection for known Balmon monitoring stations and OpenStreetMap Nominatim.
    """
    # 1. Preset check for known Balmon DIY station coordinates (high precision match)
    known_stations = [
        {"lat": -7.733139, "lon": 110.471667, "district": "Kalasan", "city": "SLEMAN", "station": "Stasiun Tetap Kalasan (Kantor Balmon)"},
        {"lat": -7.868770, "lon": 110.505050, "district": "Patuk", "city": "GUNUNG KIDUL", "station": "Pos Monitoring Patuk"},
        {"lat": -7.925000, "lon": 110.442000, "district": "Dlingo", "city": "BANTUL", "station": "Pos Monitoring Dlingo"},
        {"lat": -7.842000, "lon": 110.231000, "district": "Sentolo", "city": "KULON PROGO", "station": "Pos Monitoring Sentolo"},
        {"lat": -7.801000, "lon": 110.364000, "district": "Kraton", "city": "KOTA YOGYAKARTA", "station": "Monitoring Kota Jogja"}
    ]
    
    for ks in known_stations:
        if haversine_distance_km(lat, lon, ks["lat"], ks["lon"]) < 0.2: # within 200 meters
            return {
                "district": ks["district"],
                "city": ks["city"],
                "province": "D.I. Yogyakarta",
                "station_name": ks["station"],
                "display_name": f"{ks['district']}, {ks['city']}"
            }
            
    # 2. Query OSM Nominatim Reverse Geocoder
    import json
    import urllib.request
    
    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "BalmonYogyakarta-AIMonitoring/1.0 (balmon_jogja@kominfo.go.id)"}
    )
    
    district = ""
    city = ""
    province = "D.I. Yogyakarta"
    
    try:
        with urllib.request.urlopen(req, timeout=3.5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                addr = data.get("address", {})
                
                # Extract District (Kecamatan / Kapanewon / Kemantren)
                district = (
                    addr.get("municipality") or 
                    addr.get("city_district") or 
                    addr.get("suburb") or 
                    addr.get("town") or 
                    addr.get("village") or 
                    ""
                )
                for prefix in ["Kapanewon ", "Kecamatan ", "Kemantren ", "Kec. ", "Desa "]:
                    if district.startswith(prefix):
                        district = district[len(prefix):].strip()
                        
                # Extract City / Regency (Kabupaten / Kota)
                raw_city = (
                    addr.get("county") or 
                    addr.get("city") or 
                    addr.get("regency") or 
                    ""
                )
                for prefix in ["Kabupaten ", "Kab. ", "Kota "]:
                    if raw_city.startswith(prefix):
                        raw_city = raw_city[len(prefix):].strip()
                
                if "Gunung" in raw_city:
                    city = "GUNUNG KIDUL"
                elif "Sleman" in raw_city:
                    city = "SLEMAN"
                elif "Bantul" in raw_city:
                    city = "BANTUL"
                elif "Kulon" in raw_city:
                    city = "KULON PROGO"
                elif "Yogyakarta" in raw_city:
                    city = "KOTA YOGYAKARTA"
                else:
                    city = raw_city.upper() if raw_city else "SLEMAN"
                    
                province = addr.get("state") or "D.I. Yogyakarta"
    except Exception:
        # Fallback based on rough bounding heuristics if network is offline
        if lat < -7.85 and lon > 110.45:
            city = "GUNUNG KIDUL"
            district = "Patuk"
        elif lat < -7.82 and lon <= 110.45:
            city = "BANTUL"
            district = "Bantul"
        elif lon < 110.25:
            city = "KULON PROGO"
            district = "Wates"
        elif -7.83 <= lat <= -7.77 and 110.34 <= lon <= 110.40:
            city = "KOTA YOGYAKARTA"
            district = "Umbulharjo"
        else:
            city = "SLEMAN"
            district = "Kalasan"

    return {
        "district": district or "Kalasan",
        "city": city or "SLEMAN",
        "province": province,
        "station_name": "Stasiun Monitoring Lapangan",
        "display_name": f"{district or 'Kalasan'}, {city or 'SLEMAN'}"
    }

