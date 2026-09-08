import pytest
from app.core.peak_detector import detect_peaks

def test_detect_peaks_synthetic_signal():
    freqs = [88.0, 88.5, 89.0, 89.5, 90.0, 90.5, 91.0]
    levels = [30.0, 45.0, 70.0, 42.0, 35.0, 80.0, 40.0]
    # Peaks should be at index 2 (89.0 MHz @ 70 dBuV/m) and index 5 (90.5 MHz @ 80 dBuV/m)
    
    peaks = detect_peaks(freqs, levels)
    assert peaks == [False, False, True, False, False, True, False]

def test_detect_peaks_with_threshold():
    freqs = [88.0, 88.5, 89.0, 89.5, 90.0, 90.5, 91.0]
    levels = [30.0, 45.0, 70.0, 42.0, 35.0, 80.0, 40.0]
    
    # Threshold at 75 dBuV/m: only index 5 should pass
    peaks = detect_peaks(freqs, levels, threshold_dbuvm=75.0)
    assert peaks == [False, False, False, False, False, True, False]

def test_detect_peaks_with_frequency_range():
    freqs = [88.0, 88.5, 89.0, 89.5, 90.0, 90.5, 91.0]
    levels = [30.0, 45.0, 70.0, 42.0, 35.0, 80.0, 40.0]
    
    # Frequency range 88.0 - 89.5 MHz: only index 2 should pass
    peaks = detect_peaks(freqs, levels, start_freq_mhz=88.0, stop_freq_mhz=89.5)
    assert peaks == [False, False, True, False, False, False, False]
