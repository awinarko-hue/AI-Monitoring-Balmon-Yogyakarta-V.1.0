from typing import List, Dict, Any

FREQUENCY_BAND_PRESETS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "1. Maritim, Marabahaya (479 - 526.5 kHz)",
        "start_freq_mhz": 0.479,
        "stop_freq_mhz": 0.5265,
        "category": "Maritim"
    },
    {
        "id": 2,
        "name": "2. Radio AM (535 - 1606.5 kHz)",
        "start_freq_mhz": 0.535,
        "stop_freq_mhz": 1.6065,
        "category": "Broadcasting"
    },
    {
        "id": 3,
        "name": "3. Marabahaya (2173.5 - 2190.5 kHz)",
        "start_freq_mhz": 2.1735,
        "stop_freq_mhz": 2.1905,
        "category": "Maritim"
    },
    {
        "id": 4,
        "name": "4. Penerbangan HF, Amatir (5450 - 11400 kHz)",
        "start_freq_mhz": 5.450,
        "stop_freq_mhz": 11.400,
        "category": "Aeronautical"
    },
    {
        "id": 5,
        "name": "5. Maritim HF (26100 - 26175 kHz)",
        "start_freq_mhz": 26.100,
        "stop_freq_mhz": 26.175,
        "category": "Maritim"
    },
    {
        "id": 6,
        "name": "6. Radio FM (87.5 - 108 MHz)",
        "start_freq_mhz": 87.5,
        "stop_freq_mhz": 108.0,
        "category": "Broadcasting"
    },
    {
        "id": 7,
        "name": "7. Penerbangan VHF (108 - 137 MHz)",
        "start_freq_mhz": 108.0,
        "stop_freq_mhz": 137.0,
        "category": "Aeronautical"
    },
    {
        "id": 8,
        "name": "8. Konsesi, Maritim VHF (150 - 174 MHz)",
        "start_freq_mhz": 150.0,
        "stop_freq_mhz": 174.0,
        "category": "Maritim / Konsesi"
    },
    {
        "id": 9,
        "name": "9. Televisi VHF, DAB (174 - 230 MHz)",
        "start_freq_mhz": 174.0,
        "stop_freq_mhz": 230.0,
        "category": "Broadcasting"
    },
    {
        "id": 10,
        "name": "10. Tetap, Bergerak, Marabahaya (300 - 430 MHz)",
        "start_freq_mhz": 300.0,
        "stop_freq_mhz": 430.0,
        "category": "Bergerak Darat"
    },
    {
        "id": 11,
        "name": "11. Komrad (430 - 460 MHz)",
        "start_freq_mhz": 430.0,
        "stop_freq_mhz": 460.0,
        "category": "Komrad"
    },
    {
        "id": 12,
        "name": "12. Downlink Selular 450 (460 - 470 MHz)",
        "start_freq_mhz": 460.0,
        "stop_freq_mhz": 470.0,
        "category": "Selular"
    },
    {
        "id": 13,
        "name": "13. Televisi UHF (478 - 806 MHz)",
        "start_freq_mhz": 478.0,
        "stop_freq_mhz": 806.0,
        "category": "Broadcasting"
    },
    {
        "id": 14,
        "name": "14. Komrad, Downlink Selular 800 (806 - 880 MHz)",
        "start_freq_mhz": 851.0, # or 806.0 to 880.0
        "stop_freq_mhz": 880.0,
        "category": "Selular / Komrad"
    },
    {
        "id": 15,
        "name": "15. Downlink Selular 900 (925 - 960 MHz)",
        "start_freq_mhz": 925.0,
        "stop_freq_mhz": 960.0,
        "category": "Selular"
    },
    {
        "id": 16,
        "name": "16. Downlink Selular 1800 (1805 - 1880 MHz)",
        "start_freq_mhz": 1805.0,
        "stop_freq_mhz": 1880.0,
        "category": "Selular"
    },
    {
        "id": 17,
        "name": "17. Downlink Selular 2100 (2110 - 2170 MHz)",
        "start_freq_mhz": 2110.0,
        "stop_freq_mhz": 2170.0,
        "category": "Selular"
    },
    {
        "id": 18,
        "name": "18. Selular, Broadband 2.3 GHz (2300 - 2400 MHz)",
        "start_freq_mhz": 2300.0,
        "stop_freq_mhz": 2400.0,
        "category": "BWA / Selular"
    }
]

def get_preset_by_id(preset_id: int) -> Dict[str, Any]:
    for p in FREQUENCY_BAND_PRESETS:
        if p["id"] == preset_id:
            return p
    return None
