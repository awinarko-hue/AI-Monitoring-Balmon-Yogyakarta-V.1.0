import io
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import openpyxl

def parse_date_value(val: Any) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val if isinstance(val, date) else val.date()
    if isinstance(val, str):
        val = val.strip()
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y"]:
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None

def parse_sims_excel(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Parse exported SIMS database Excel file dynamically by header names.
    Expected headers:
    FREQ, CLNT_NAME, SID_LAT, SID_LONG, SERVICE, SUBSERVICE, 
    EMIS_CLASS_1, EQUIP_TYPE, STN_NAME, CITY, MASA_LAKU, TGL_QUERY
    """
    wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
    ws = wb.active
    
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("File SIMS Excel kosong")
        
    header_row = rows[0]
    header_map = {}
    for col_idx, cell in enumerate(header_row):
        if cell is not None:
            norm_name = str(cell).strip().upper()
            header_map[norm_name] = col_idx
            
    # Key column names to look for
    freq_col = header_map.get("FREQ") or header_map.get("FREKUENSI") or header_map.get("TX_FREQ")
    client_col = header_map.get("CLNT_NAME") or header_map.get("PENGGUNA") or header_map.get("NAMA PENGGUNA") or header_map.get("CLIENT_NAME")
    lat_col = header_map.get("SID_LAT") or header_map.get("LATITUDE") or header_map.get("LAT")
    lon_col = header_map.get("SID_LONG") or header_map.get("LONGITUDE") or header_map.get("LONG") or header_map.get("LON")
    
    service_col = header_map.get("SERVICE") or header_map.get("DINAS")
    subservice_col = header_map.get("SUBSERVICE") or header_map.get("SUB_DINAS")
    emission_col = header_map.get("EMIS_CLASS_1") or header_map.get("KELAS_EMISI") or header_map.get("EMISSION")
    equip_col = header_map.get("EQUIP_TYPE") or header_map.get("TIPE_PERANGKAT")
    station_col = header_map.get("STN_NAME") or header_map.get("NAMA_STASIUN")
    city_col = header_map.get("CITY") or header_map.get("KABUPATEN") or header_map.get("KOTA")
    expiry_col = header_map.get("MASA_LAKU") or header_map.get("EXPIRY_DATE") or header_map.get("TGL_KADALUARSA")
    query_col = header_map.get("TGL_QUERY") or header_map.get("QUERY_DATE")
    
    if freq_col is None or client_col is None:
        raise ValueError(f"Header wajib 'FREQ' dan 'CLNT_NAME' tidak ditemukan di file SIMS. Headers ditemukan: {list(header_map.keys())}")
        
    records = []
    dataset_query_date = None
    
    for r_idx in range(1, len(rows)):
        row = rows[r_idx]
        if not row or row[freq_col] is None:
            continue
            
        try:
            freq_raw = row[freq_col]
            if isinstance(freq_raw, str):
                freq_raw = freq_raw.replace(",", ".").strip()
            freq_val = float(freq_raw)
        except (ValueError, TypeError):
            continue
            
        client_name = str(row[client_col]).strip() if row[client_col] is not None else "Unknown"
        
        # Coordinates
        lat_val = 0.0
        lon_val = 0.0
        if lat_col is not None and row[lat_col] is not None:
            try:
                lat_val = float(str(row[lat_col]).replace(",", ".").strip())
            except (ValueError, TypeError):
                pass
        if lon_col is not None and row[lon_col] is not None:
            try:
                lon_val = float(str(row[lon_col]).replace(",", ".").strip())
            except (ValueError, TypeError):
                pass
                
        service_val = str(row[service_col]).strip() if (service_col is not None and row[service_col] is not None) else None
        subservice_val = str(row[subservice_col]).strip() if (subservice_col is not None and row[subservice_col] is not None) else None
        emission_val = str(row[emission_col]).strip() if (emission_col is not None and row[emission_col] is not None) else None
        equip_val = str(row[equip_col]).strip() if (equip_col is not None and row[equip_col] is not None) else None
        station_val = str(row[station_col]).strip() if (station_col is not None and row[station_col] is not None) else None
        city_val = str(row[city_col]).strip() if (city_col is not None and row[city_col] is not None) else None
        
        expiry_val = parse_date_value(row[expiry_col]) if expiry_col is not None else None
        query_val = parse_date_value(row[query_col]) if query_col is not None else None
        
        if query_val and dataset_query_date is None:
            dataset_query_date = query_val
            
        records.append({
            "freq_mhz": freq_val,
            "client_name": client_name,
            "latitude": lat_val,
            "longitude": lon_val,
            "service": service_val,
            "subservice": subservice_val,
            "emission_class": emission_val,
            "equipment_type": equip_val,
            "station_name": station_val,
            "city": city_val,
            "expiry_date": expiry_val,
            "query_date": query_val or date.today()
        })
        
    return {
        "filename": filename,
        "query_date": dataset_query_date or date.today(),
        "total_records": len(records),
        "records": records
    }
