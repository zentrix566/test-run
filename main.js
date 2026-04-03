import FitParser from 'fit-file-parser';

// Constants
const SPORT_NAMES = {
  0: '通用', 1: '跑步', 2: '骑行', 3: '游泳',
  4: '力量训练', 5: '徒步', 6: '步行', 7: '室内骑行',
  8: '公开水域游泳', 9: 'Swimrun', 10: '越野跑',
  11: '单板滑雪', 12: '越野滑雪', 13: '高山滑雪',
  14: '划船', 15: '登山', 28: 'HIIT', 30: '桨板',
};

// Global variables
let map = null;
let polyline = null;
let hrChart = null;
let speedChart = null;

// Initialize map
function initMap() {
  if (!map) {
    map = L.map('map');
    // Use China-based open tile provider that doesn't need API key
    L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; Stadia Maps',
      maxZoom: 20
    }).addTo(map);
  }
  return map;
}

// Setup drag and drop
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');

uploadArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', (e) => {
  e.preventDefault();
  uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadArea.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    processFile(files[0]);
  }
});

fileInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) {
    processFile(e.target.files[0]);
  }
});

function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m ${secs}s`;
}

function formatPace(distanceKm, seconds) {
  if (distanceKm <= 0 || seconds <= 0) return '-';
  const paceSecPerKm = seconds / distanceKm;
  const minutes = Math.floor(paceSecPerKm / 60);
  const secondsRemain = Math.floor(paceSecPerKm % 60);
  return `${minutes}'${secondsRemain.toString().padStart(2, '0')}"`;
}

// fit-file-parser already converts to degrees, no need to convert again!
function convertSemicircleToDegrees(value) {
  // If it's still in semicircle units (original fit format), convert: return value * (180.0 / 2147483648);
  // fit-file-parser already does the conversion, so just return as-is
  return value;
}

function processFile(file) {
  document.getElementById('loading').style.display = 'block';
  document.getElementById('resultContainer').style.display = 'none';
  document.getElementById('uploadArea').style.display = 'none';

  const reader = new FileReader();
  reader.onload = function(e) {
    const arrayBuffer = e.target.result;
    console.log(`📁 File loaded: ${(arrayBuffer.byteLength / 1024 / 1024).toFixed(2)} MB`);

    const fitParser = new FitParser({
      force: true,
      speedUnit: 'm/s',
      lengthUnit: 'm',
      temperatureUnit: 'celsius',
      elapsedRecordField: true,
      mode: 'object'
    });

    console.log('⏳ Starting parsing...');
    const startTime = performance.now();

    fitParser.parse(arrayBuffer, function(error, data) {
      const endTime = performance.now();
      console.log(`✅ Parsing completed in ${(endTime - startTime).toFixed(0)} ms`);

      if (error) {
        console.error('❌ Parse error:', error);
        alert('解析错误: ' + error.message);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('uploadArea').style.display = 'block';
        return;
      }

      // Get data - try plural then singular
      const sessions = data.sessions || data.session || [];
      const laps = data.laps || data.lap || [];
      const records = data.records || data.record || [];

      console.log(`📊 Stats:
  - Sessions: ${sessions.length || 0}
  - Laps: ${laps.length || 0}
  - Records: ${records.length || 0}
      `);

      processFitData({sessions, laps, records});
      console.log('🎉 Rendering completed');
      document.getElementById('loading').style.display = 'none';
      document.getElementById('resultContainer').style.display = 'flex';
    });
  };
  reader.readAsArrayBuffer(file);
}

function processFitData(data) {
  // Get session summary
  const {sessions, records} = data;
  const session = sessions && sessions.length > 0 ? sessions[0] : null;
  const recordsList = records || [];
  console.log(`🔍 Processing: ${recordsList.length} total record points`);

  // Initialize map
  const map = initMap();

  // Clear existing polyline
  if (polyline) {
    map.removeLayer(polyline);
  }

  // Process track points - one pass optimization
  const latlngs = [];
  const chartData = [];
  let cumDist = 0;
  let prevLatlng = null;

  // Sample for map if too many points (improve rendering performance)
  const maxMapPoints = 2000;
  const sampleRatio = Math.max(1, Math.floor(recordsList.length / maxMapPoints));
  console.log(`🗺️  Map point sampling: ratio 1:${sampleRatio} (target ~${maxMapPoints} points)`);
  let pointCounter = 0;

  const processingStart = performance.now();
  recordsList.forEach(record => {
    if (record.position_lat !== undefined && record.position_long !== undefined) {
      const lat = convertSemicircleToDegrees(record.position_lat);
      const lng = convertSemicircleToDegrees(record.position_long);

      // Calculate cumulative distance for chart
      let distance = 0;
      if (prevLatlng) {
        const dLat = (lat - prevLatlng[0]) * Math.PI / 180;
        const dLng = (lng - prevLatlng[1]) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos((prevLatlng[0]) * Math.PI / 180) * Math.cos(lat * Math.PI / 180) *
                Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        distance = 6371 * c; // km
        cumDist += distance;
      }

      // Add to chart data regardless of sampling
      chartData.push({
        lat, lng,
        distanceKm: cumDist,
        heartRate: record.heart_rate || null,
        speed: record.speed || null,
        altitude: record.altitude || null
      });

      // Sample for map to improve performance
      if (pointCounter % sampleRatio === 0) {
        latlngs.push([lat, lng]);
      }
      pointCounter++;

      prevLatlng = [lat, lng];
    }
  });

  const processingEnd = performance.now();
  console.log(`✓ Point processing done in ${(processingEnd - processingStart).toFixed(0)} ms -> ${latlngs.length} map points, ${chartData.length} chart points`);

  // Add polyline to map
  if (latlngs.length > 0) {
    console.log('🗺️  Rendering map...');
    polyline = L.polyline(latlngs, {color: '#2196F3', weight: 4, opacity: 0.8}).addTo(map);

    // Add start/end markers
    const fullPoints = chartData.filter(p => p !== undefined);
    if (fullPoints.length > 0) {
      L.marker([fullPoints[0].lat, fullPoints[0].lng]).addTo(map).bindPopup('起点');
      if (fullPoints.length > 1) {
        L.marker([fullPoints[fullPoints.length - 1].lat, fullPoints[fullPoints.length - 1].lng]).addTo(map).bindPopup('终点');
      }
    }

    // Fix: invalidate size after container becomes visible
    // Do it multiple times to ensure it works
    setTimeout(() => {
      map.invalidateSize();
      map.fitBounds(polyline.getBounds());
    }, 50);
    setTimeout(() => {
      map.invalidateSize();
      map.fitBounds(polyline.getBounds());
    }, 200);
  } else {
    console.warn('⚠️ No latlngs found for polyline');
  }

  // Update statistics
  updateStats(session, recordsList);

  // Create charts
  console.log('📊 Creating charts...');
  createCharts(chartData);
  console.log('✅ All done!');
}

function updateStats(session, records) {
  if (!session) {
    return;
  }

  // Sport
  const sportNum = session.sport;
  const sportName = SPORT_NAMES[sportNum] || ('类型 ' + sportNum);
  document.getElementById('stat-sport').textContent = sportName;

  // Start time (convert to Beijing timezone)
  if (session.start_time) {
    const dt = new Date(session.start_time);
    // session.start_time is already seconds since epoch
    const bjDt = new Date(dt.getTime() + 8 * 60 * 60 * 1000);
    const dateStr = bjDt.toISOString().split('T')[0];
    const timeStr = bjDt.toTimeString().slice(0, 5);
    document.getElementById('stat-date').textContent = dateStr;
  } else {
    document.getElementById('stat-date').textContent = '-';
  }

  // Distance
  const distance = session.total_distance || 0;
  const distanceKmStr = (distance / 1000).toFixed(2);
  document.getElementById('stat-distance').textContent = distanceKmStr + ' km';

  // Time
  const elapsed = session.total_elapsed_time || 0;
  document.getElementById('stat-time').textContent = formatTime(elapsed);

  // Pace
  const distanceKm = distance / 1000;
  document.getElementById('stat-pace').textContent = formatPace(distanceKm, elapsed);

  // Calories
  const calories = session.total_calories || '-';
  document.getElementById('stat-calories').textContent = calories + (calories !== '-' ? ' kcal' : '');

  // Heart rate
  const avgHr = session.avg_heart_rate || '-';
  const maxHr = session.max_heart_rate || '-';
  document.getElementById('stat-avg-hr').textContent = avgHr !== '-' ? avgHr + ' bpm' : '-';
  document.getElementById('stat-max-hr').textContent = maxHr !== '-' ? maxHr + ' bpm' : '-';

  // Ascent
  const ascent = session.total_ascent || '-';
  document.getElementById('stat-ascent').textContent = ascent !== '-' ? ascent + ' m' : '-';

  // Strides
  const strides = session.total_strides || '-';
  document.getElementById('stat-strides').textContent = strides;
}

function createCharts(chartData) {
  // Filter out points without position
  const validData = chartData.filter(p => p.distanceKm !== undefined);

  // Sample data for chart (max ~100 points for smooth chart)
  const sampleInterval = Math.max(1, Math.floor(validData.length / 100));
  const distanceKm = [];
  const heartRate = [];
  const speedKmh = [];

  for (let i = 0; i < validData.length; i += sampleInterval) {
    const p = validData[i];
    if (p.heartRate !== null && p.heartRate > 0) {
      distanceKm.push(p.distanceKm.toFixed(1));
      heartRate.push(p.heartRate);
    }
    if (p.speed !== null) {
      speedKmh.push(p.speed * 3.6); // m/s to km/h
    }
  }

  // Destroy old charts
  if (hrChart) {
    hrChart.destroy();
  }
  if (speedChart) {
    speedChart.destroy();
  }

  // Heart Rate Chart
  const ctxHr = document.getElementById('hrChart').getContext('2d');
  hrChart = new Chart(ctxHr, {
    type: 'line',
    data: {
      labels: distanceKm,
      datasets: [{
        label: '心率 (bpm)',
        data: heartRate,
        borderColor: '#f44336',
        backgroundColor: 'rgba(244, 67, 54, 0.1)',
        fill: true,
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: '心率随距离变化' },
        legend: { display: false }
      },
      scales: {
        x: {
          title: { display: true, text: '距离 (km)' },
          ticks: {
            maxTicksLimit: 10, // Only show 10 ticks on X axis
            autoSkip: true
          }
        },
        y: {
          min: heartRate.length > 0 ? Math.min(...heartRate) - 10 : 60,
          max: heartRate.length > 0 ? Math.max(...heartRate) + 10 : 200
        }
      }
    }
  });

  // Speed Chart
  const ctxSpeed = document.getElementById('speedChart').getContext('2d');
  speedChart = new Chart(ctxSpeed, {
    type: 'line',
    data: {
      labels: distanceKm,
      datasets: [{
        label: '速度 (km/h)',
        data: speedKmh,
        borderColor: '#4CAF50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        fill: true,
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: '速度随距离变化' },
        legend: { display: false }
      },
      scales: {
        x: {
          title: { display: true, text: '距离 (km)' },
          ticks: {
            maxTicksLimit: 10, // Only show 10 ticks on X axis
            autoSkip: true
          }
        },
        y: { title: { display: true, text: '速度 (km/h)' }}
      }
    }
  });
}

// Initialize
initMap();
