from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
import bisect
from app.core.geo import haversine_distance_km, is_within_bounding_box
from app.core.peak_detector import detect_peaks

class IdentificationEngine:
    def __init__(
        self,
        monitoring_lat: Optional[float] = None,
        monitoring_lon: Optional[float] = None,
        monitoring_date: Optional[date] = None,
        detection_radius_km: float = 50.0,
        threshold_dbuvm: float = 50.0,
        freq_tolerance_mhz: float = 0.05
    ):
        self.monitoring_lat = monitoring_lat if monitoring_lat is not None else -7.7828
        self.monitoring_lon = monitoring_lon if monitoring_lon is not None else 110.3670
        self.monitoring_date = monitoring_date or date.today()
        self.detection_radius_km = detection_radius_km
        self.threshold_dbuvm = threshold_dbuvm
        self.freq_tolerance_mhz = freq_tolerance_mhz

    def find_best_sims_match(
        self, 
        freq: float, 
        sorted_sims: List[Dict[str, Any]],
        sims_freqs: List[float]
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """
        Find closest SIMS station matching frequency (within tolerance) and within detection radius.
        Uses bisect for O(log N) lookup.
        """
        left_idx = bisect.bisect_left(sims_freqs, freq - self.freq_tolerance_mhz)
        right_idx = bisect.bisect_right(sims_freqs, freq + self.freq_tolerance_mhz)
        
        best_match = None
        min_dist = float("inf")
        
        for i in range(left_idx, right_idx):
            rec = sorted_sims[i]
            rec_lat = rec.get("latitude")
            rec_lon = rec.get("longitude")
            if rec_lat is not None and rec_lon is not None:
                dist = haversine_distance_km(self.monitoring_lat, self.monitoring_lon, rec_lat, rec_lon)
                if dist <= self.detection_radius_km and dist < min_dist:
                    min_dist = dist
                    best_match = rec
                    
        if best_match is not None:
            return (best_match, min_dist)
        return None

    def find_best_manual_match(
        self, 
        freq: float, 
        sorted_manual: List[Dict[str, Any]],
        manual_freqs: List[float]
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """
        Find closest manual station matching frequency within tolerance using bisect.
        """
        left_idx = bisect.bisect_left(manual_freqs, freq - self.freq_tolerance_mhz)
        right_idx = bisect.bisect_right(manual_freqs, freq + self.freq_tolerance_mhz)
        
        best_match = None
        min_dist = float("inf")
        
        for i in range(left_idx, right_idx):
            stn = sorted_manual[i]
            stn_lat = stn.get("latitude")
            stn_lon = stn.get("longitude")
            if stn_lat is not None and stn_lon is not None:
                dist = haversine_distance_km(self.monitoring_lat, self.monitoring_lon, stn_lat, stn_lon)
                if dist <= self.detection_radius_km and dist < min_dist:
                    min_dist = dist
                    best_match = stn
                    
        if best_match is not None:
            return (best_match, min_dist)
        return None

    def classify_status(
        self,
        level_dbuvm: float,
        is_peak: bool,
        matched_sims: Optional[Dict[str, Any]],
        matched_manual: Optional[Dict[str, Any]],
        sims_dist: Optional[float],
        manual_dist: Optional[float]
    ) -> Tuple[str, str, Optional[float], str, Optional[Dict[str, Any]]]:
        """
        Determine identification status and name.
        Returns: (status, identified_name, distance_km, matched_source, matched_entity)
        """
        # 1. Check manual station match first (priority override)
        if matched_manual is not None:
            status = matched_manual.get("status_legality") or "Legal"
            name = matched_manual.get("client_name") or "Stasiun Manual"
            return (status, name, manual_dist, "MANUAL", matched_manual)
            
        # 2. Check SIMS database match
        if matched_sims is not None:
            name = matched_sims.get("client_name") or "SIMS Licensee"
            service_desc = (matched_sims.get("service") or "").upper()
            subservice_desc = (matched_sims.get("subservice") or "").upper()
            
            # Check if international service
            if "INTERNASIONAL" in service_desc or subservice_desc == "INTERNASIONAL":
                status = "Internasional"
            else:
                expiry = matched_sims.get("expiry_date")
                if expiry is not None:
                    # Convert string to date if needed
                    if isinstance(expiry, str):
                        try:
                            expiry = datetime.strptime(expiry, "%Y-%m-%d").date()
                        except ValueError:
                            try:
                                expiry = datetime.strptime(expiry, "%d/%m/%Y").date()
                            except ValueError:
                                expiry = None
                                
                    if expiry and expiry < self.monitoring_date:
                        status = "Kadaluarsa"
                    else:
                        status = "Legal"
                else:
                    status = "Legal"
                    
            # Check if signal is off air (license exists in radius, but signal is below threshold)
            if level_dbuvm < self.threshold_dbuvm:
                status = "Off Air"
                
            return (status, name, sims_dist, "SIMS", matched_sims)
            
        # 3. No match in SIMS or Manual
        if level_dbuvm >= self.threshold_dbuvm:
            if is_peak:
                return ("Belum Diketahui", "Belum Teridentifikasi", None, "NONE", None)
            else:
                return ("Clear", "-", None, "NONE", None)
        else:
            return ("Clear", "-", None, "NONE", None)

    def process_session(
        self,
        scan_points: List[Dict[str, Any]],
        sims_records: List[Dict[str, Any]],
        manual_stations: List[Dict[str, Any]],
        start_freq_mhz: Optional[float] = None,
        stop_freq_mhz: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute full auto-identification for all scan points with O(N log M) efficiency.
        """
        if not scan_points:
            return []
            
        # Filter points first if range specified to avoid processing out-of-band points
        filtered_points = []
        for p in scan_points:
            freq = p["frequency_mhz"]
            if start_freq_mhz is not None and freq < start_freq_mhz:
                continue
            if stop_freq_mhz is not None and freq > stop_freq_mhz:
                continue
            filtered_points.append(p)
            
        if not filtered_points:
            return []
            
        # Extract lists for peak detection
        freqs = [p["frequency_mhz"] for p in filtered_points]
        levels = [p["level_dbuvm"] for p in filtered_points]
        
        peak_flags = detect_peaks(
            freqs, 
            levels, 
            threshold_dbuvm=None,
            start_freq_mhz=start_freq_mhz, 
            stop_freq_mhz=stop_freq_mhz
        )
        
        # Sort SIMS and manual records by frequency for binary search
        sorted_sims = sorted([r for r in sims_records if r.get("freq_mhz") is not None], key=lambda x: x["freq_mhz"])
        sims_freqs = [r["freq_mhz"] for r in sorted_sims]
        
        sorted_manual = sorted([m for m in manual_stations if m.get("freq_mhz") is not None], key=lambda x: x["freq_mhz"])
        manual_freqs = [m["freq_mhz"] for m in sorted_manual]
        
        results = []
        
        for idx, pt in enumerate(filtered_points):
            freq = pt["frequency_mhz"]
            level = pt["level_dbuvm"]
            is_peak = peak_flags[idx]
                
            # Find closest matching records with O(log N) bisect
            sims_match_res = self.find_best_sims_match(freq, sorted_sims, sims_freqs)
            manual_match_res = self.find_best_manual_match(freq, sorted_manual, manual_freqs)
            
            matched_sims = sims_match_res[0] if sims_match_res else None
            sims_dist = sims_match_res[1] if sims_match_res else None
            
            matched_manual = manual_match_res[0] if manual_match_res else None
            manual_dist = manual_match_res[1] if manual_match_res else None
            
            status, name, dist, source, entity = self.classify_status(
                level_dbuvm=level,
                is_peak=is_peak,
                matched_sims=matched_sims,
                matched_manual=matched_manual,
                sims_dist=sims_dist,
                manual_dist=manual_dist
            )
            
            item = {
                "scan_point_id": pt.get("id"),
                "frequency_mhz": freq,
                "level_dbuvm": level,
                "is_peak": is_peak,
                "identified_name": name,
                "status": status,
                "distance_km": round(dist, 2) if dist is not None else None,
                "matched_source": source,
                "service": entity.get("service") if entity else None,
                "subservice": entity.get("subservice") if entity else None,
                "emission_class": entity.get("emission_class") if entity else None,
                "station_latitude": entity.get("latitude") if entity else None,
                "station_longitude": entity.get("longitude") if entity else None,
                "station_city": entity.get("city") if entity else None,
                "matched_sims_id": matched_sims.get("id") if matched_sims else None,
                "matched_manual_id": matched_manual.get("id") if matched_manual else None,
            }
            results.append(item)
            
        return results

    def filter_marker_results(
        self, 
        results: List[Dict[str, Any]], 
        marker_mode: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Filter results according to selected Marker view mode:
        - 'all': All signals that have SIMS/Manual matches OR active peaks
        - 'peak': Only peak signals above threshold
        - 'offair': Only off-air stations
        - 'blm_diketahui': Only unknown signals above threshold
        - 'all+blm_diketahui': Identified + unknown peaks
        - 'all+offair': Identified + off-air
        - 'all+offair+blm_diketahui': Identified + off-air + unknown peaks
        """
        mode = marker_mode.lower().replace(" ", "_")
        filtered = []
        
        for r in results:
            status = r["status"]
            is_peak = r["is_peak"]
            level = r["level_dbuvm"]
            is_identified = status in ["Legal", "Kadaluarsa", "Tidak Sesuai ISR", "Ilegal", "Internasional"]
            
            if mode == "all":
                if (is_identified and level >= self.threshold_dbuvm) or (is_peak and level >= self.threshold_dbuvm):
                    filtered.append(r)
            elif mode == "peak":
                if is_peak and level >= self.threshold_dbuvm:
                    filtered.append(r)
            elif mode == "offair":
                if status == "Off Air":
                    filtered.append(r)
            elif mode in ["blm_diketahui", "blm diketahui"]:
                if status == "Belum Diketahui" and is_peak and level >= self.threshold_dbuvm:
                    filtered.append(r)
            elif mode in ["all+blm_diketahui", "all+blm diketahui"]:
                if (is_identified and level >= self.threshold_dbuvm) or (status == "Belum Diketahui" and is_peak and level >= self.threshold_dbuvm):
                    filtered.append(r)
            elif mode in ["all+offair", "all+off air"]:
                if (is_identified and level >= self.threshold_dbuvm) or (status == "Off Air"):
                    filtered.append(r)
            elif mode in ["all+offair+blm_diketahui", "all+offair+blm diketahui", "all+off_air+blm_diketahui"]:
                if (is_identified and level >= self.threshold_dbuvm) or (status == "Off Air") or (status == "Belum Diketahui" and is_peak and level >= self.threshold_dbuvm):
                    filtered.append(r)
            else:
                filtered.append(r)
                
        return filtered
