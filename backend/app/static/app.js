// AI Monitoring Balmon Yogyakarta - Client Application Logic

const API_BASE = '/api';
let authToken = localStorage.getItem('balmon_auth_token') || '';
let currentUser = { username: 'admin', full_name: 'Administrator Balmon DIY', role: 'admin' };

// Application State
let sessionsList = [];
let currentSessionId = null;
let currentSessionData = null;
let currentResults = [];
let allPresets = [];
let spectrumChartInstance = null;
let leafletMapInstance = null;

// Table Pagination & Filter State
let currentTablePage = 1;
const PAGE_SIZE = 25;
let currentSearchQuery = '';

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', async () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  
  await checkAuthAndLogin();
  setupEventListeners();
  await loadPresets();
  await loadSessions();
  await loadConfigSettings();
});

// Authentication helper
async function checkAuthAndLogin() {
  if (!authToken) {
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      });
      if (res.ok) {
        const data = await res.json();
        authToken = data.access_token;
        localStorage.setItem('balmon_auth_token', authToken);
        currentUser = { username: data.username, full_name: data.full_name, role: data.role };
        updateUserUI();
      }
    } catch (e) {
      console.error('Auto login error:', e);
    }
  } else {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        currentUser = await res.json();
        updateUserUI();
      } else {
        authToken = '';
        localStorage.removeItem('balmon_auth_token');
        await checkAuthAndLogin();
      }
    } catch (e) {
      console.error('Check me error:', e);
    }
  }
}

function updateUserUI() {
  const nameEl = document.getElementById('displayUserName');
  const roleEl = document.getElementById('displayUserRole');
  if (nameEl) nameEl.textContent = currentUser.full_name;
  if (roleEl) roleEl.textContent = currentUser.role === 'admin' ? 'PPFR Ahli Muda / Admin' : 'Petugas Monitoring';
}

function authHeaders() {
  return authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
}

// Event Listeners Setup
function setupEventListeners() {
  // Session dropdown
  document.getElementById('sessionSelect').addEventListener('change', async (e) => {
    if (e.target.value) {
      await selectSession(parseInt(e.target.value));
    }
  });

  // Preset selector
  document.getElementById('presetSelect').addEventListener('change', (e) => {
    const val = e.target.value;
    if (val !== 'custom') {
      const p = allPresets.find(item => item.id == val);
      if (p) {
        document.getElementById('inputStartFreq').value = p.start_freq_mhz;
        document.getElementById('inputStopFreq').value = p.stop_freq_mhz;
        // Dynamically update spectrum chart and table to the selected frequency band
        updateSpectrumChart();
        renderTable();
      }
    }
  });

  // Start / Stop frequency & Threshold dynamic input changes
  document.getElementById('inputStartFreq').addEventListener('input', () => {
    updateSpectrumChart();
    renderTable();
  });
  document.getElementById('inputStopFreq').addEventListener('input', () => {
    updateSpectrumChart();
    renderTable();
  });
  document.getElementById('inputThreshold').addEventListener('input', () => {
    updateSpectrumChart();
    renderTable();
  });

  // Auto Identifikasi Button
  document.getElementById('btnRunIdentification').addEventListener('click', async () => {
    await runIdentification();
  });

  // Marker filter select
  document.getElementById('markerFilterSelect').addEventListener('change', () => {
    renderTable();
  });

  // Search input
  document.getElementById('tableSearch').addEventListener('input', (e) => {
    currentSearchQuery = e.target.value.toLowerCase();
    currentTablePage = 1;
    renderTable();
  });

  // Modal open buttons
  document.getElementById('btnNewScan').addEventListener('click', () => openModal('modalUploadScan'));
  document.getElementById('btnOpenSims').addEventListener('click', () => {
    openModal('modalSims');
    loadSimsDatasets();
  });
  document.getElementById('btnOpenManual').addEventListener('click', () => {
    openModal('modalManual');
    loadManualStations();
  });
  document.getElementById('btnOpenMap').addEventListener('click', () => {
    openModal('modalMap');
    setTimeout(initOrUpdateMap, 200);
  });
  document.getElementById('btnOpenSettings').addEventListener('click', () => {
    openModal('modalSettings');
    loadConfigSettings();
  });

  // Export buttons
  document.getElementById('btnExport').addEventListener('click', () => downloadRolExcel());
  document.getElementById('btnExportExcelQuick').addEventListener('click', () => downloadRolExcel());
  document.getElementById('btnExportDocxQuick').addEventListener('click', () => downloadDocxReport());

  // Forms
  document.getElementById('formUploadScan').addEventListener('submit', handleUploadScan);
  document.getElementById('fileSimsInput').addEventListener('change', handleUploadSims);
  document.getElementById('formAddManual').addEventListener('submit', handleAddManualStation);
  document.getElementById('formSettings').addEventListener('submit', handleSaveSettings);

  // Scan file dropzone
  const dropzone = document.getElementById('dropzoneScan');
  const fileInput = document.getElementById('fileScanInput');
  dropzone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      document.getElementById('selectedScanFileName').textContent = fileInput.files[0].name;
    }
  });
}

// Load 18 presets
async function loadPresets() {
  try {
    const res = await fetch(`${API_BASE}/identification/presets`);
    if (res.ok) {
      allPresets = await res.json();
      const select = document.getElementById('presetSelect');
      select.innerHTML = '<option value="custom">Pilih Preset Pita Frekuensi (18 Pita Balmon)...</option>';
      allPresets.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.name;
        select.appendChild(opt);
      });
    }
  } catch (e) {
    console.error('Load presets error:', e);
  }
}

// Load Sessions
async function loadSessions() {
  try {
    const res = await fetch(`${API_BASE}/scan/sessions`, { headers: authHeaders() });
    if (res.ok) {
      sessionsList = await res.json();
      const select = document.getElementById('sessionSelect');
      select.innerHTML = '';
      
      if (sessionsList.length === 0) {
        select.innerHTML = '<option value="">Belum ada sesi monitoring</option>';
        return;
      }
      
      sessionsList.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = `${s.session_name} (${s.monitoring_date})`;
        select.appendChild(opt);
      });

      if (!currentSessionId && sessionsList.length > 0) {
        await selectSession(sessionsList[0].id);
      }
    }
  } catch (e) {
    console.error('Load sessions error:', e);
  }
}

// Select a session
async function selectSession(sessionId) {
  currentSessionId = sessionId;
  document.getElementById('sessionSelect').value = sessionId;
  
  try {
    // 1. Fetch detail session with scan points
    const res = await fetch(`${API_BASE}/scan/sessions/${sessionId}`, { headers: authHeaders() });
    if (res.ok) {
      currentSessionData = await res.json();
      updateSessionMetadataUI();
      
      // Set input defaults
      document.getElementById('inputStartFreq').value = currentSessionData.start_frequency_mhz || '';
      document.getElementById('inputStopFreq').value = currentSessionData.stop_frequency_mhz || '';
      document.getElementById('inputThreshold').value = currentSessionData.threshold_dbuvm || 50;
      document.getElementById('inputRadius').value = currentSessionData.detection_radius_km || 50;
      document.getElementById('markerFilterSelect').value = currentSessionData.marker_filter || 'all';
      
      // 2. Fetch identification results
      await loadIdentificationResults(sessionId);
    }
  } catch (e) {
    console.error('Select session error:', e);
  }
}

function updateSessionMetadataUI() {
  if (!currentSessionData) return;
  document.getElementById('metaSessionName').textContent = currentSessionData.session_name;
  document.getElementById('metaSptNumber').textContent = currentSessionData.spt_number || '-';
  document.getElementById('metaDateTime').textContent = currentSessionData.monitoring_date || '-';
  
  // Auto resolve accurate location if coordinate matches Kalasan Balmon
  let locText = `${currentSessionData.district ? currentSessionData.district + ', ' : ''}${currentSessionData.city || 'Yogyakarta'}`;
  if (Math.abs(currentSessionData.latitude - (-7.733139)) < 0.005 && Math.abs(currentSessionData.longitude - 110.471667) < 0.005) {
    locText = 'Kalasan, SLEMAN';
  }
  document.getElementById('metaLocation').textContent = locText;
  document.getElementById('metaCoordinates').textContent = `${currentSessionData.latitude.toFixed(6)}, ${currentSessionData.longitude.toFixed(6)}`;
  document.getElementById('metaOfficer').textContent = currentSessionData.officer_name || 'Petugas Balmon';
  document.getElementById('badgeDeviceType').textContent = currentSessionData.device_type;
}

// Load identification results for session
async function loadIdentificationResults(sessionId) {
  try {
    const res = await fetch(`${API_BASE}/identification/results/${sessionId}`, { headers: authHeaders() });
    if (res.ok) {
      const summary = await res.json();
      currentResults = summary.results;
      
      // Update statistics
      document.getElementById('statTotalSignals').textContent = summary.total_signals;
      document.getElementById('statTotalPeaks').textContent = summary.total_peaks;
      
      const b = summary.status_breakdown || {};
      document.getElementById('statLegal').textContent = b['Legal'] || 0;
      document.getElementById('statExpired').textContent = b['Kadaluarsa'] || 0;
      document.getElementById('statUnknown').textContent = (b['Belum Diketahui'] || 0) + (b['Ilegal'] || 0);
      
      // Update Spectrum Chart & Table
      updateSpectrumChart();
      renderTable();
    }
  } catch (e) {
    console.error('Load identification error:', e);
  }
}

// Run Auto Identification
async function runIdentification() {
  if (!currentSessionId) {
    showToast('Pilih atau buat sesi monitoring terlebih dahulu!', 'error');
    return;
  }
  
  const startF = parseFloat(document.getElementById('inputStartFreq').value) || null;
  const stopF = parseFloat(document.getElementById('inputStopFreq').value) || null;
  const th = parseFloat(document.getElementById('inputThreshold').value) || 50.0;
  const rad = parseFloat(document.getElementById('inputRadius').value) || 50.0;
  const markerMode = document.getElementById('markerFilterSelect').value || 'all';
  
  const btn = document.getElementById('btnRunIdentification');
  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="loader" class="spin"></i> Memproses...';
  if (window.lucide) lucide.createIcons();
  
  try {
    const res = await fetch(`${API_BASE}/identification/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders()
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        start_frequency_mhz: startF,
        stop_frequency_mhz: stopF,
        threshold_dbuvm: th,
        detection_radius_km: rad,
        marker_filter: markerMode
      })
    });
    
    if (res.ok) {
      showToast('Auto Identifikasi Spektrum Berhasil Selesai!', 'success');
      await selectSession(currentSessionId);
    } else {
      const err = await res.json();
      showToast(err.detail || 'Gagal menjalankan identifikasi', 'error');
    }
  } catch (e) {
    showToast('Terjadi kesalahan koneksi server', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="play"></i> Auto Identifikasi';
    if (window.lucide) lucide.createIcons();
  }
}

// Update Spectrum Analyzer Chart (Chart.js)
function updateSpectrumChart() {
  if (!currentSessionData || !currentSessionData.points) return;
  
  const ctx = document.getElementById('spectrumChart').getContext('2d');
  const threshold = parseFloat(document.getElementById('inputThreshold').value) || 50.0;
  const startFVal = parseFloat(document.getElementById('inputStartFreq').value);
  const stopFVal = parseFloat(document.getElementById('inputStopFreq').value);
  
  let allPoints = currentSessionData.points || [];
  let points = allPoints;
  
  // Filter points to selected frequency range (preset / inputs)
  if (!isNaN(startFVal) && !isNaN(stopFVal) && startFVal < stopFVal) {
    const subset = allPoints.filter(p => p.frequency_mhz >= startFVal && p.frequency_mhz <= stopFVal);
    if (subset.length > 0) {
      points = subset;
    }
  }
  
  const labels = points.map(p => p.frequency_mhz.toFixed(2));
  const dataLevels = points.map(p => p.level_dbuvm);
  const thresholdData = points.map(() => threshold);
  
  // Point styling for Peaks & Identified stations
  const pointColors = [];
  const pointRadius = [];
  
  const resultMap = {};
  currentResults.forEach(r => {
    resultMap[r.frequency_mhz.toFixed(2)] = r;
  });
  
  points.forEach(p => {
    const key = p.frequency_mhz.toFixed(2);
    const idInfo = resultMap[key];
    
    if (idInfo) {
      if (idInfo.status === 'Legal') {
        pointColors.push('#10b981');
        pointRadius.push(6);
      } else if (idInfo.status === 'Kadaluarsa') {
        pointColors.push('#f59e0b');
        pointRadius.push(6);
      } else if (idInfo.status === 'Belum Diketahui' || idInfo.status === 'Ilegal' || idInfo.status === 'Tidak Sesuai ISR') {
        pointColors.push('#f43f5e');
        pointRadius.push(6);
      } else if (idInfo.status === 'Off Air') {
        pointColors.push('#64748b');
        pointRadius.push(4);
      } else {
        pointColors.push('transparent');
        pointRadius.push(0);
      }
    } else if (p.is_peak) {
      pointColors.push('#06b6d4');
      pointRadius.push(4);
    } else {
      pointColors.push('transparent');
      pointRadius.push(0);
    }
  });

  if (spectrumChartInstance) {
    spectrumChartInstance.destroy();
  }

  // Gradient fill for spectrum
  const gradient = ctx.createLinearGradient(0, 0, 0, 350);
  gradient.addColorStop(0, 'rgba(6, 182, 212, 0.45)');
  gradient.addColorStop(0.5, 'rgba(6, 182, 212, 0.15)');
  gradient.addColorStop(1, 'rgba(6, 182, 212, 0.0)');

  spectrumChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Threshold (dBuV/m)',
          data: thresholdData,
          borderColor: '#ef4444',
          borderWidth: 2,
          borderDash: [6, 6],
          pointRadius: 0,
          fill: false,
          tension: 0,
          order: 1
        },
        {
          label: 'Level Sinyal (dBuV/m)',
          data: dataLevels,
          borderColor: '#06b6d4',
          borderWidth: 2,
          backgroundColor: gradient,
          fill: true,
          tension: 0.1,
          pointBackgroundColor: pointColors,
          pointBorderColor: pointColors,
          pointRadius: pointRadius,
          pointHoverRadius: 8,
          order: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 250 },
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleColor: '#06b6d4',
          bodyColor: '#f8fafc',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 12,
          callbacks: {
            title: function(items) {
              return `Frekuensi: ${items[0].label} MHz`;
            },
            afterBody: function(items) {
              const freqKey = items[0].label;
              const info = resultMap[freqKey];
              if (info) {
                return [
                  `Identifikasi: ${info.identified_name}`,
                  `Status: ${info.status}`,
                  `Jarak: ${info.distance_km ? info.distance_km + ' km' : '-'}`,
                  `Dinas: ${info.service || '-'}`
                ];
              }
              return [];
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#94a3b8', maxTicksLimit: 20, font: { family: 'JetBrains Mono', size: 11 } },
          title: { display: true, text: 'Frekuensi (MHz)', color: '#94a3b8', font: { weight: 'bold' } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 11 } },
          title: { display: true, text: 'Field Strength (dBuV/m)', color: '#94a3b8', font: { weight: 'bold' } }
        }
      }
    }
  });
}

// Render Identification Table
function renderTable() {
  const tbody = document.getElementById('tableBody');
  const markerMode = document.getElementById('markerFilterSelect').value;
  const startF = parseFloat(document.getElementById('inputStartFreq').value);
  const stopF = parseFloat(document.getElementById('inputStopFreq').value);
  
  let filtered = currentResults.filter(r => {
    // 0. Filter by active frequency range
    if (!isNaN(startF) && !isNaN(stopF) && startF < stopF) {
      if (r.frequency_mhz < startF || r.frequency_mhz > stopF) return false;
    }

    // 1. Marker filter mode
    if (markerMode === 'peak' && !r.is_peak) return false;
    if (markerMode === 'offair' && r.status !== 'Off Air') return false;
    if (markerMode === 'blm_diketahui' && r.status !== 'Belum Diketahui') return false;
    if (markerMode === 'all+blm_diketahui' && !(r.status in {Legal:1, Kadaluarsa:1, 'Belum Diketahui':1, Ilegal:1, 'Tidak Sesuai ISR':1})) return false;
    if (markerMode === 'all+offair' && !(r.status in {Legal:1, Kadaluarsa:1, 'Off Air':1, Ilegal:1, 'Tidak Sesuai ISR':1})) return false;
    
    // 2. Search query filter
    if (currentSearchQuery) {
      const q = currentSearchQuery;
      const match = (
        r.frequency_mhz.toString().includes(q) ||
        r.identified_name.toLowerCase().includes(q) ||
        r.status.toLowerCase().includes(q) ||
        (r.service && r.service.toLowerCase().includes(q)) ||
        (r.station_city && r.station_city.toLowerCase().includes(q))
      );
      if (!match) return false;
    }
    return true;
  });

  document.getElementById('tableInfo').textContent = `Menampilkan ${filtered.length} dari ${currentResults.length} hasil identifikasi`;
  
  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center text-muted" style="padding: 2rem;">Tidak ada data yang cocok dengan filter rentang frekuensi atau pencarian</td></tr>`;
    renderPagination(0);
    return;
  }

  // Pagination slice
  const startIdx = (currentTablePage - 1) * PAGE_SIZE;
  const pageItems = filtered.slice(startIdx, startIdx + PAGE_SIZE);

  tbody.innerHTML = '';
  pageItems.forEach((r, idx) => {
    const tr = document.createElement('tr');
    
    let badgeClass = 'badge-legal';
    if (r.status === 'Kadaluarsa') badgeClass = 'badge-expired';
    else if (r.status === 'Belum Diketahui') badgeClass = 'badge-unknown';
    else if (r.status === 'Ilegal' || r.status === 'Tidak Sesuai ISR') badgeClass = 'badge-illegal';
    else if (r.status === 'Off Air') badgeClass = 'badge-offair';

    tr.innerHTML = `
      <td class="text-center text-muted">${startIdx + idx + 1}</td>
      <td class="font-mono font-bold text-cyan">${r.frequency_mhz.toFixed(4)}</td>
      <td class="font-mono">${r.level_dbuvm.toFixed(1)}</td>
      <td class="text-center">${r.is_peak ? '<span class="badge-peak-marker">Peak</span>' : '-'}</td>
      <td class="font-bold">${r.identified_name}</td>
      <td><span class="badge ${badgeClass}">${r.status}</span></td>
      <td class="font-mono">${r.distance_km ? r.distance_km.toFixed(1) : '-'}</td>
      <td>${r.station_city || '-'}</td>
      <td class="text-muted">${r.service || '-'}</td>
      <td class="text-center text-muted"><small>${r.matched_source}</small></td>
    `;
    tbody.appendChild(tr);
  });

  renderPagination(filtered.length);
}

function renderPagination(totalItems) {
  const container = document.getElementById('paginationControls');
  container.innerHTML = '';
  const totalPages = Math.ceil(totalItems / PAGE_SIZE);
  if (totalPages <= 1) return;

  for (let p = 1; p <= totalPages; p++) {
    const btn = document.createElement('button');
    btn.className = `page-btn ${p === currentTablePage ? 'active' : ''}`;
    btn.textContent = p;
    btn.addEventListener('click', () => {
      currentTablePage = p;
      renderTable();
    });
    container.appendChild(btn);
  }
}

// Leaflet Map Initialization
function initOrUpdateMap() {
  if (!currentSessionData) return;
  
  const mapEl = document.getElementById('leafletMap');
  const lat = currentSessionData.latitude || -7.733139;
  const lon = currentSessionData.longitude || 110.471667;
  const radiusKm = currentSessionData.detection_radius_km || 50.0;

  if (!leafletMapInstance) {
    leafletMapInstance = L.map(mapEl).setView([lat, lon], 10);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(leafletMapInstance);
  } else {
    leafletMapInstance.setView([lat, lon], 10);
    leafletMapInstance.eachLayer((layer) => {
      if (layer instanceof L.Marker || layer instanceof L.Circle) {
        leafletMapInstance.removeLayer(layer);
      }
    });
  }

  // Monitoring Station Marker & 50km Detection Radius Circle
  L.circle([lat, lon], {
    radius: radiusKm * 1000,
    color: '#06b6d4',
    fillColor: '#06b6d4',
    fillOpacity: 0.08,
    dashArray: '5, 5'
  }).addTo(leafletMapInstance);

  const monIcon = L.divIcon({
    className: 'custom-mon-marker',
    html: '<div style="background:#3b82f6; width:16px; height:16px; border-radius:50%; border:3px solid #fff; box-shadow:0 0 10px #3b82f6;"></div>'
  });

  L.marker([lat, lon], { icon: monIcon })
    .addTo(leafletMapInstance)
    .bindPopup(`<strong>Stasiun Monitoring Balmon</strong><br>${currentSessionData.monitoring_station}<br>Lat: ${lat.toFixed(6)}, Lon: ${lon.toFixed(6)}`)
    .openPopup();

  // Plot matched transmitter stations from results
  currentResults.forEach(r => {
    if (r.station_latitude && r.station_longitude) {
      let color = '#10b981';
      if (r.status === 'Kadaluarsa') color = '#f59e0b';
      else if (r.status === 'Belum Diketahui' || r.status === 'Ilegal') color = '#f43f5e';
      
      const txIcon = L.divIcon({
        className: 'custom-tx-marker',
        html: `<div style="background:${color}; width:12px; height:12px; border-radius:50%; border:2px solid #fff;"></div>`
      });

      L.marker([r.station_latitude, r.station_longitude], { icon: txIcon })
        .addTo(leafletMapInstance)
        .bindPopup(`
          <strong>${r.identified_name}</strong><br>
          Frekuensi: ${r.frequency_mhz} MHz<br>
          Status: <b>${r.status}</b><br>
          Jarak: ${r.distance_km ? r.distance_km + ' km' : '-'}<br>
          Kota: ${r.station_city || '-'}
        `);
    }
  });

  leafletMapInstance.invalidateSize();
}

// Upload Scan Handler
async function handleUploadScan(e) {
  e.preventDefault();
  const fileInput = document.getElementById('fileScanInput');
  if (!fileInput.files || fileInput.files.length === 0) {
    showToast('Pilih file hasil scan terlebih dahulu!', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('session_name', document.getElementById('uploadSessionName').value);
  formData.append('device_type', document.getElementById('uploadDeviceType').value);
  formData.append('spt_number', document.getElementById('uploadSptNumber').value);
  formData.append('officer_name', document.getElementById('uploadOfficerName').value);
  formData.append('latitude', document.getElementById('uploadLatitude').value);
  formData.append('longitude', document.getElementById('uploadLongitude').value);
  formData.append('city', document.getElementById('uploadCity').value);
  formData.append('district', document.getElementById('uploadDistrict').value);

  const btn = document.getElementById('btnSubmitScan');
  btn.disabled = true;
  btn.innerHTML = 'Mengunggah & Mem-parsing...';

  try {
    const res = await fetch(`${API_BASE}/scan/upload`, {
      method: 'POST',
      headers: authHeaders(),
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      showToast(`Scan ${data.device_type} Berhasil Diimpor (${data.total_points} titik data)!`, 'success');
      closeModal('modalUploadScan');
      await loadSessions();
      await selectSession(data.id);
      await runIdentification();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Gagal mengunggah file scan', 'error');
    }
  } catch (err) {
    showToast('Koneksi terputus saat mengunggah', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="upload"></i> Upload & Parse';
    if (window.lucide) lucide.createIcons();
  }
}

// SIMS Excel Upload & Management
async function loadSimsDatasets() {
  try {
    const res = await fetch(`${API_BASE}/sims/datasets`);
    if (res.ok) {
      const list = await res.json();
      const tbody = document.getElementById('simsDatasetList');
      if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Belum ada dataset SIMS terunggah</td></tr>';
        return;
      }
      tbody.innerHTML = '';
      list.forEach(ds => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${ds.dataset_name}</strong></td>
          <td>${ds.query_date || '-'}</td>
          <td>${ds.uploaded_by || '-'}</td>
          <td>${ds.total_records} izin</td>
          <td>${ds.is_active ? '<span class="badge badge-legal">Aktif</span>' : '<span class="badge badge-offair">Arsip</span>'}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (e) {
    console.error('Load SIMS datasets error:', e);
  }
}

async function handleUploadSims(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  showToast('Mengunggah & memproses database SIMS...', 'info');

  try {
    const res = await fetch(`${API_BASE}/sims/upload`, {
      method: 'POST',
      headers: authHeaders(),
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`Database SIMS berhasil diperbarui (${data.total_records} data izin)!`, 'success');
      await loadSimsDatasets();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Gagal memproses file SIMS', 'error');
    }
  } catch (e) {
    showToast('Koneksi gagal saat unggah SIMS', 'error');
  }
}

// Manual Station Management
async function loadManualStations() {
  try {
    const res = await fetch(`${API_BASE}/sims/manual-stations`);
    if (res.ok) {
      const list = await res.json();
      const tbody = document.getElementById('manualStationList');
      if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Belum ada data stasiun manual</td></tr>';
        return;
      }
      tbody.innerHTML = '';
      list.forEach(stn => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td class="font-mono font-bold text-cyan">${stn.freq_mhz} MHz</td>
          <td>${stn.client_name}</td>
          <td class="font-mono text-muted">${stn.latitude}, ${stn.longitude}</td>
          <td>${stn.service || '-'}</td>
          <td><span class="badge badge-legal">${stn.status_legality}</span></td>
          <td><button class="btn btn-sm btn-glass" onclick="deleteManualStation(${stn.id})">Hapus</button></td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (e) {
    console.error('Load manual stations error:', e);
  }
}

async function handleAddManualStation(e) {
  e.preventDefault();
  const freq = parseFloat(document.getElementById('manFreq').value);
  const client = document.getElementById('manClient').value;
  const lat = parseFloat(document.getElementById('manLat').value);
  const lon = parseFloat(document.getElementById('manLon').value);
  const status = document.getElementById('manStatus').value;

  try {
    const res = await fetch(`${API_BASE}/sims/manual-stations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ freq_mhz: freq, client_name: client, latitude: lat, longitude: lon, status_legality: status })
    });
    if (res.ok) {
      showToast('Stasiun tambahan berhasil disimpan!', 'success');
      document.getElementById('manFreq').value = '';
      document.getElementById('manClient').value = '';
      await loadManualStations();
    }
  } catch (e) {
    showToast('Gagal menambah stasiun manual', 'error');
  }
}

window.deleteManualStation = async function(id) {
  if (!confirm('Hapus stasiun manual ini?')) return;
  try {
    const res = await fetch(`${API_BASE}/sims/manual-stations/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
    });
    if (res.ok) {
      showToast('Stasiun manual berhasil dihapus', 'info');
      await loadManualStations();
    }
  } catch (e) {
    showToast('Gagal menghapus stasiun', 'error');
  }
};

// Configuration Settings
async function loadConfigSettings() {
  try {
    const res = await fetch(`${API_BASE}/settings`);
    if (res.ok) {
      const cfg = await res.json();
      document.getElementById('setLatMax').value = cfg.lat_max;
      document.getElementById('setLatMin').value = cfg.lat_min;
      document.getElementById('setLonMin').value = cfg.lon_min;
      document.getElementById('setLonMax').value = cfg.lon_max;
      document.getElementById('setDefaultThreshold').value = cfg.default_threshold_dbuvm;
      document.getElementById('setDefaultRadius').value = cfg.default_radius_km;
    }
  } catch (e) {
    console.error('Load settings error:', e);
  }
}

async function handleSaveSettings(e) {
  e.preventDefault();
  const payload = {
    lat_max: parseFloat(document.getElementById('setLatMax').value),
    lat_min: parseFloat(document.getElementById('setLatMin').value),
    lon_min: parseFloat(document.getElementById('setLonMin').value),
    lon_max: parseFloat(document.getElementById('setLonMax').value),
    default_threshold_dbuvm: parseFloat(document.getElementById('setDefaultThreshold').value),
    default_radius_km: parseFloat(document.getElementById('setDefaultRadius').value)
  };

  try {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast('Pengaturan Balmon berhasil diperbarui!', 'success');
      closeModal('modalSettings');
    }
  } catch (e) {
    showToast('Gagal menyimpan pengaturan', 'error');
  }
}

// Download ROL Excel
function downloadRolExcel() {
  if (!currentSessionId) {
    showToast('Pilih sesi monitoring terlebih dahulu!', 'error');
    return;
  }
  window.open(`${API_BASE}/report/export-rol/${currentSessionId}`, '_blank');
  showToast('Mengunduh Laporan Rekaman Operasi Lapangan (ROL)...', 'info');
}

// Download DOCX Report
function downloadDocxReport() {
  if (!currentSessionId) {
    showToast('Pilih sesi monitoring terlebih dahulu!', 'error');
    return;
  }
  window.open(`${API_BASE}/report/export-docx/${currentSessionId}`, '_blank');
  showToast('Mengunduh Laporan Kegiatan DOCX/PDF...', 'info');
}

// Modal helper functions
window.openModal = function(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('open');
};

window.closeModal = function(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('open');
};

// Toast notification helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let iconName = 'info';
  if (type === 'success') iconName = 'check-circle';
  else if (type === 'error') iconName = 'alert-triangle';
  
  toast.innerHTML = `<i data-lucide="${iconName}"></i> <span>${message}</span>`;
  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s ease reverse forwards';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Preset Lokasi Stasiun Balmon & Reverse Geocoding Helper
const BALMON_LOCATION_PRESETS = {
  kalasan: { lat: -7.733139, lon: 110.471667, district: 'Kalasan', city: 'SLEMAN', name: 'Stasiun Tetap Kalasan (Kantor Balmon)' },
  patuk: { lat: -7.868770, lon: 110.505050, district: 'Patuk', city: 'GUNUNG KIDUL', name: 'Pos Monitoring Patuk' },
  dlingo: { lat: -7.925000, lon: 110.442000, district: 'Dlingo', city: 'BANTUL', name: 'Pos Monitoring Dlingo' },
  sentolo: { lat: -7.842000, lon: 110.231000, district: 'Sentolo', city: 'KULON PROGO', name: 'Pos Monitoring Sentolo' },
  kraton: { lat: -7.801000, lon: 110.364000, district: 'Kraton', city: 'KOTA YOGYAKARTA', name: 'Monitoring Kota Jogja' }
};

window.setMonitoringLocationPreset = function(presetKey) {
  const p = BALMON_LOCATION_PRESETS[presetKey];
  if (!p) return;
  document.getElementById('uploadLatitude').value = p.lat.toFixed(6);
  document.getElementById('uploadLongitude').value = p.lon.toFixed(6);
  document.getElementById('uploadDistrict').value = p.district;
  document.getElementById('uploadCity').value = p.city;
  
  const badge = document.getElementById('geoStatusBadge');
  if (badge) {
    badge.style.display = 'inline-block';
    badge.textContent = `📍 ${p.district}, ${p.city}`;
  }
};

let geocodeDebounceTimer = null;
window.triggerReverseGeocodeDebounced = function() {
  clearTimeout(geocodeDebounceTimer);
  geocodeDebounceTimer = setTimeout(() => {
    performManualGeocode();
  }, 500);
};

window.performManualGeocode = async function() {
  const lat = parseFloat(document.getElementById('uploadLatitude').value);
  const lon = parseFloat(document.getElementById('uploadLongitude').value);
  if (isNaN(lat) || isNaN(lon)) return;
  
  const badge = document.getElementById('geoStatusBadge');
  if (badge) {
    badge.style.display = 'inline-block';
    badge.textContent = '⏳ Mendeteksi...';
  }
  
  // 1. Check known presets first
  for (const k in BALMON_LOCATION_PRESETS) {
    const p = BALMON_LOCATION_PRESETS[k];
    if (Math.abs(lat - p.lat) < 0.005 && Math.abs(lon - p.lon) < 0.005) {
      document.getElementById('uploadDistrict').value = p.district;
      document.getElementById('uploadCity').value = p.city;
      if (badge) badge.textContent = `📍 ${p.district}, ${p.city}`;
      return;
    }
  }
  
  // 2. Fetch from backend reverse-geocode endpoint
  try {
    const res = await fetch(`${API_BASE}/scan/reverse-geocode?latitude=${lat}&longitude=${lon}`);
    if (res.ok) {
      const data = await res.json();
      if (data.district) document.getElementById('uploadDistrict').value = data.district;
      if (data.city) document.getElementById('uploadCity').value = data.city;
      if (badge) badge.textContent = `📍 ${data.district || ''}, ${data.city || ''}`;
      return;
    }
  } catch (err) {
    console.warn('Geocoding API error:', err);
  }
  
  // 3. Fallback direct OSM Nominatim
  try {
    const osmRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`);
    if (osmRes.ok) {
      const osmData = await osmRes.json();
      const addr = osmData.address || {};
      let d = addr.municipality || addr.city_district || addr.suburb || addr.town || addr.village || 'Kalasan';
      ['Kapanewon ', 'Kecamatan ', 'Kemantren ', 'Kec. '].forEach(pfx => { if (d.startsWith(pfx)) d = d.substring(pfx.length); });
      
      let c = addr.county || addr.city || addr.regency || 'SLEMAN';
      ['Kabupaten ', 'Kab. ', 'Kota '].forEach(pfx => { if (c.startsWith(pfx)) c = c.substring(pfx.length); });
      c = c.toUpperCase();
      
      document.getElementById('uploadDistrict').value = d;
      document.getElementById('uploadCity').value = c;
      if (badge) badge.textContent = `📍 ${d}, ${c}`;
    }
  } catch (e) {
    if (badge) badge.textContent = '📍 Manual';
  }
};

