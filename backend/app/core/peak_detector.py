from typing import List, Dict, Any, Tuple

def detect_peaks(
    frequencies: List[float], 
    levels: List[float], 
    threshold_dbuvm: float = None,
    start_freq_mhz: float = None,
    stop_freq_mhz: float = None
) -> List[bool]:
    """
    Detect local peak markers from spectrum scan points.
    Matches Excel VBA formula: RC[-1] > R[-1]C[-1] AND RC[-1] > R[1]C[-1]
    (A point is a Peak if its level is strictly greater than its previous and next neighbor).
    
    Optional filters:
    - start_freq_mhz and stop_freq_mhz (only evaluate within frequency range)
    - threshold_dbuvm (if provided, peak must also be >= threshold)
    """
    n = len(levels)
    is_peak = [False] * n
    
    if n < 3:
        return is_peak
        
    for i in range(1, n - 1):
        freq = frequencies[i]
        
        # Check start / stop range if specified
        if start_freq_mhz is not None and freq < start_freq_mhz:
            continue
        if stop_freq_mhz is not None and freq > stop_freq_mhz:
            continue
            
        # Peak condition: higher than left and right neighbor
        if levels[i] > levels[i - 1] and levels[i] > levels[i + 1]:
            if threshold_dbuvm is not None:
                if levels[i] >= threshold_dbuvm:
                    is_peak[i] = True
            else:
                is_peak[i] = True
                
    return is_peak
