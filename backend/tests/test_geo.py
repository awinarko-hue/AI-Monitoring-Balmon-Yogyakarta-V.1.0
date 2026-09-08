import pytest
import math
from app.core.geo import haversine_distance_km, is_within_bounding_box

def test_haversine_same_point():
    assert haversine_distance_km(-7.733139, 110.471667, -7.733139, 110.471667) == 0.0

def test_haversine_known_distance():
    # Tugu Yogyakarta (-7.782889, 110.367072) to Candi Prambanan (-7.752020, 110.491467)
    # Approx distance is around 14.1 km
    dist = haversine_distance_km(-7.782889, 110.367072, -7.752020, 110.491467)
    assert 13.5 < dist < 14.8

def test_bounding_box_inside():
    # Balmon Yogyakarta Office (-7.733139, 110.471667)
    lat_min = -8.213584
    lat_max = -7.503037
    lon_min = 109.375246
    lon_max = 111.321684
    
    assert is_within_bounding_box(-7.733139, 110.471667, lat_min, lat_max, lon_min, lon_max) is True

def test_bounding_box_outside():
    # Jakarta location (-6.2088, 106.8456)
    lat_min = -8.213584
    lat_max = -7.503037
    lon_min = 109.375246
    lon_max = 111.321684
    
    assert is_within_bounding_box(-6.2088, 106.8456, lat_min, lat_max, lon_min, lon_max) is False
