import io
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def generate_rol_excel(
    session_data: Dict[str, Any],
    results: List[Dict[str, Any]],
    template_bytes: Optional[bytes] = None
) -> bytes:
    """
    Generate standard ROL (Rekaman Operasi Lapangan) Excel file.
    Uses dynamic header mapping to populate columns reliably.
    """
    if template_bytes:
        wb = openpyxl.load_workbook(io.BytesIO(template_bytes))
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Rekaman_Operasi_Lapangan"
        
        # Build standard Balmon ROL Header
        ws.merge_cells("A1:N1")
        ws["A1"] = "REKAMAN OPERASI LAPANGAN (ROL) PENGAMATAN SPEKTRUM FREKUENSI RADIO"
        ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
        
        ws.merge_cells("A2:N2")
        ws["A2"] = f"BALAI MONITOR SPEKTRUM FREKUENSI RADIO KELAS I YOGYAKARTA"
        ws["A2"].font = Font(name="Calibri", size=11, bold=True, color="333333")
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
        
        # Metadata table
        ws["A4"] = "Nama Sesi / Kegiatan:"
        ws["C4"] = session_data.get("session_name", "-")
        ws["A5"] = "Nomor SPT:"
        ws["C5"] = session_data.get("spt_number", "-")
        ws["A6"] = "Petugas Pelaksana:"
        ws["C6"] = session_data.get("officer_name", "-")
        ws["A7"] = "Tanggal Monitoring:"
        ws["C7"] = str(session_data.get("monitoring_date", date.today()))
        
        ws["H4"] = "Stasiun Monitoring:"
        ws["J4"] = session_data.get("monitoring_station", "SMSN")
        ws["H5"] = "Koordinat Lokasi:"
        ws["J5"] = f"Lat: {session_data.get('latitude', '-')}, Lon: {session_data.get('longitude', '-')}"
        ws["H6"] = "Alat Ukur / Format:"
        ws["J6"] = session_data.get("device_type", "TCI")
        ws["H7"] = "Threshold & Radius:"
        ws["J7"] = f"{session_data.get('threshold_dbuvm', 50)} dBuV/m | Radius {session_data.get('detection_radius_km', 50)} km"
        
        for r in range(4, 8):
            ws[f"A{r}"].font = Font(bold=True)
            ws[f"H{r}"].font = Font(bold=True)
            
        # Table headers
        headers = [
            "NO", "FREKUENSI (MHz)", "LEVEL (dBuV/m)", "MARKER PUNCAK", 
            "IDENTIFIKASI / NAMA PENGGUNA", "STATUS LEGALITAS", "JARAK (KM)",
            "LOKASI / KABUPATEN", "DINAS (SERVICE)", "SUB DINAS", "KELAS EMISI", "SUMBER DATA"
        ]
        
        header_row = 10
        for col_idx, h_text in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=h_text)
            cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            
        thin_border = Border(
            left=Side(style='thin', color='D3D3D3'),
            right=Side(style='thin', color='D3D3D3'),
            top=Side(style='thin', color='D3D3D3'),
            bottom=Side(style='thin', color='D3D3D3')
        )
        
        # Populate data rows
        for idx, res in enumerate(results, 1):
            curr_row = header_row + idx
            ws.cell(row=curr_row, column=1, value=idx).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=2, value=res.get("frequency_mhz", 0.0)).number_format = "0.0000"
            ws.cell(row=curr_row, column=3, value=res.get("level_dbuvm", 0.0)).number_format = "0.00"
            ws.cell(row=curr_row, column=4, value="Peak" if res.get("is_peak") else "-").alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=5, value=res.get("identified_name", "-"))
            
            # Status styling
            status_val = res.get("status", "-")
            status_cell = ws.cell(row=curr_row, column=6, value=status_val)
            status_cell.alignment = Alignment(horizontal="center")
            
            if status_val == "Legal":
                status_cell.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid") # Soft Green
                status_cell.font = Font(color="385723", bold=True)
            elif status_val == "Kadaluarsa":
                status_cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid") # Soft Yellow/Orange
                status_cell.font = Font(color="B25900", bold=True)
            elif status_val in ["Ilegal", "Tidak Sesuai ISR"]:
                status_cell.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid") # Soft Red
                status_cell.font = Font(color="C00000", bold=True)
            elif status_val == "Belum Diketahui":
                status_cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                status_cell.font = Font(color="595959", bold=True)
            elif status_val == "Off Air":
                status_cell.fill = PatternFill(start_color="EDEDED", end_color="EDEDED", fill_type="solid")
                status_cell.font = Font(color="7F7F7F")
                
            dist_val = res.get("distance_km")
            ws.cell(row=curr_row, column=7, value=dist_val if dist_val is not None else "-")
            ws.cell(row=curr_row, column=8, value=res.get("station_city") or "-")
            ws.cell(row=curr_row, column=9, value=res.get("service") or "-")
            ws.cell(row=curr_row, column=10, value=res.get("subservice") or "-")
            ws.cell(row=curr_row, column=11, value=res.get("emission_class") or "-")
            ws.cell(row=curr_row, column=12, value=res.get("matched_source") or "-").alignment = Alignment(horizontal="center")
            
            for c in range(1, 13):
                ws.cell(row=curr_row, column=c).border = thin_border
                
        # Auto adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 11), 35)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
