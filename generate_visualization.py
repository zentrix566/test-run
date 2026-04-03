#!/usr/bin/env python3
"""Generate static HTML visualization from CSV GPS data."""

import sys

def generate_html(csv_path, output_path):
    """Generate static HTML with embedded GPS data."""

    # Read CSV and format as JS array
    points_js = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 7:
                continue
            try:
                lat = float(parts[2]) if parts[2] else None
                lon = float(parts[3]) if parts[3] else None
                alt = float(parts[4]) if parts[4] else None
                hr = float(parts[5]) if parts[5] else None
                speed = float(parts[6]) if parts[6] else None
                if lat is not None and lon is not None:
                    points_js.append(f"  [{lat}, {lon}, {hr}, {speed}]")
            except ValueError:
                continue

    points_str = ",\n".join(points_js)

    html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>运动轨迹可视化 - 42.4km 跑步 2026-03-29</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: #f5f5f5; }
.header { background: #fff; padding: 16px 20px; border-bottom: 1px solid #ddd; }
.header h1 { font-size: 20px; color: #333; }
.header p { color: #666; margin-top: 4px; }
.container { display: flex; flex-wrap: wrap; padding: 16px; gap: 16px; }
.map-container { flex: 2; min-width: 600px; height: 500px; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }
#map { width: 100%; height: 100%; }
.sidebar { flex: 1; min-width: 280px; display: flex; flex-direction: column; gap: 16px; }
.stats-card { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.stats-card h3 { font-size: 14px; color: #666; margin-bottom: 12px; text-transform: uppercase; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.stat-item { text-align: center; padding: 10px; background: #f8f9fa; border-radius: 6px; }
.stat-label { font-size: 12px; color: #666; }
.stat-value { font-size: 20px; font-weight: bold; color: #333; margin-top: 4px; }
.chart-card { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: 260px; }
canvas { width: 100%; height: 100%; }
@media (max-width: 900px) {
  .container { flex-direction: column; }
  .map-container { min-width: auto; }
}
.leaflet-container { background: #f0f0f0; }
</style>
</head>
<body>

<div class="header">
  <h1>🏃 运动轨迹可视化</h1>
  <p>42.40 公里跑步 · 2026年3月29日 · 北京时间</p>
</div>

<div class="container">
  <div class="map-container">
    <div id="map"></div>
  </div>

  <div class="sidebar">
    <div class="stats-card">
      <h3>运动数据</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-label">距离</div>
          <div class="stat-value">42.40<span style="font-size:12px;"> km</span></div>
        </div>
        <div class="stat-item">
          <div class="stat-label">时间</div>
          <div class="stat-value">4:11<span style="font-size:12px;"> h</span></div>
        </div>
        <div class="stat-item">
          <div class="stat-label">平均配速</div>
          <div class="stat-value">5'53"<span style="font-size:12px;"> /km</span></div>
        </div>
        <div class="stat-item">
          <div class="stat-label">卡路里</div>
          <div class="stat-value">3745<span style="font-size:12px;"> kcal</span></div>
        </div>
        <div class="stat-item">
          <div class="stat-label">平均心率</div>
          <div class="stat-value">153<span style="font-size:12px;"> bpm</span></div>
        </div>
        <div class="stat-item">
          <div class="stat-label">最大心率</div>
          <div class="stat-value">161<span style="font-size:12px;"> bpm</span></div>
        </div>
        <div class="stat-item">
          <div class="stat-label">总爬升</div>
          <div class="stat-value">47<span style="font-size:12px;"> m</span></div>
        </div>
        <div class="stat-item">
          <div class="stat-label">总步数</div>
          <div class="stat-value">22479</div>
        </div>
      </div>
    </div>

    <div class="chart-card">
      <canvas id="hrChart"></canvas>
    </div>

    <div class="chart-card">
      <canvas id="speedChart"></canvas>
    </div>
  </div>
</div>

<script>
// GPS 轨迹数据
var trackData = [
{POINTS}
];

// Filter out null points
var trackPoints = trackData.filter(p => !isNaN(p[0]) && !isNaN(p[1]));

// Initialize map
var map = L.map('map');
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
  maxZoom: 19
}).addTo(map);

// Create polyline
var latlngs = trackPoints.map(p => [p[0], p[1]]);
var polyline = L.polyline(latlngs, {color: '#2196F3', weight: 4, opacity: 0.8}).addTo(map);

// Fit bounds
if (latlngs.length > 0) {
  map.fitBounds(polyline.getBounds());
}

// Add start/end markers
if (latlngs.length > 0) {
  L.marker(latlngs[0]).addTo(map).bindPopup('起点').openPopup();
  L.marker(latlngs[latlngs.length - 1]).addTo(map).bindPopup('终点');
}

// Prepare data for charts - sample every N points to avoid overloading
var sampleInterval = Math.max(1, Math.floor(trackPoints.length / 100));
var distanceKm = [];
var heartRate = [];
var speedKmh = [];

var cumDist = 0;
var prevLatlng = null;

for (var i = 0; i < trackPoints.length; i += sampleInterval) {
  var p = trackPoints[i];
  var lat = p[0], lng = p[1], hr = p[2], sp = p[3];

  if (prevLatlng && hr !== null && hr > 0) {
    // Approximate distance from previous point
    var dLat = (lat - prevLatlng[0]) * Math.PI / 180;
    var dLng = (lng - prevLatlng[1]) * Math.PI / 180;
    var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos((prevLatlng[0]) * Math.PI / 180) * Math.cos(lat * Math.PI / 180) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    var dist = 6371 * c; // Earth radius in km
    cumDist += dist;

    if (!isNaN(hr) && hr > 0) {
      distanceKm.push(cumDist.toFixed(1));
      heartRate.push(hr);
      speedKmh.push(sp);
    }
  }
  prevLatlng = [lat, lng];
}

// Heart Rate Chart
var ctxHr = document.getElementById('hrChart').getContext('2d');
new Chart(ctxHr, {
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
      x: { title: { display: true, text: '距离 (km)' }},
      y: { min: Math.min(...heartRate) - 10, max: Math.max(...heartRate) + 10 }
    }
  }
});

// Speed Chart
var ctxSpeed = document.getElementById('speedChart').getContext('2d');
new Chart(ctxSpeed, {
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
      x: { title: { display: true, text: '距离 (km)' }},
      y: { title: { display: true, text: '速度 (km/h)' }}
    }
  }
});
</script>
</body>
</html>
'''

    html = html_template.replace('{POINTS}', points_str)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated {output_path} with {len(points_js)} GPS points embedded")
    return True

if __name__ == '__main__':
    csv_path = 'fit_export.csv'
    output_path = 'visualization.html'
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    generate_html(csv_path, output_path)
