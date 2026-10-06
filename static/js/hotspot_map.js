/**
 * CleanTrack AI - Garbage Hotspot Monitoring Map Script
 * Leaflet.js + OpenStreetMap + Scikit-Learn DBSCAN Clustering Visualizer
 */

let hotspotMap = null;
let markersLayerGroup = null;
let clustersLayerGroup = null;
let currentHotspotData = null;

// Initial coordinates (Bengaluru urban center)
const DEFAULT_CENTER = [12.9650, 77.6150];

document.addEventListener('DOMContentLoaded', () => {
  initHotspotMap();
  loadHotspotData();
  setupMapFilters();
});

function initHotspotMap() {
  const mapElem = document.getElementById('hotspotMapCanvas');
  if (!mapElem) return;

  hotspotMap = L.map('hotspotMapCanvas').setView(DEFAULT_CENTER, 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors | CleanTrack AI Geospatial Engine'
  }).addTo(hotspotMap);

  markersLayerGroup = L.layerGroup().addTo(hotspotMap);
  clustersLayerGroup = L.layerGroup().addTo(hotspotMap);

  setTimeout(() => {
    hotspotMap.invalidateSize();
  }, 400);
}

async function loadHotspotData() {
  const loader = document.getElementById('mapLoader');
  if (loader) loader.style.display = 'block';

  // Extract filter parameters
  const category = document.getElementById('filterCategory') ? document.getElementById('filterCategory').value : 'all';
  const status = document.getElementById('filterStatus') ? document.getElementById('filterStatus').value : 'all';
  const priority = document.getElementById('filterPriority') ? document.getElementById('filterPriority').value : 'all';
  const eps = document.getElementById('filterEps') ? document.getElementById('filterEps').value : '700';

  const url = `/api/admin/hotspots?category=${category}&status=${status}&priority=${priority}&eps=${eps}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to retrieve hotspot clustering data.');
    const data = await res.json();

    currentHotspotData = data;
    renderHotspotMapVisuals(data);
    renderHotspotSidePanel(data);

  } catch (err) {
    console.error(err);
    showToast(err.message || 'Error loading hotspot map.', 'error');
  } finally {
    if (loader) loader.style.display = 'none';
  }
}

function renderHotspotMapVisuals(data) {
  if (!hotspotMap || !markersLayerGroup || !clustersLayerGroup) return;

  markersLayerGroup.clearLayers();
  clustersLayerGroup.clearLayers();

  const bounds = [];

  // 1. Render DBSCAN Clusters
  if (data.clusters && data.clusters.length > 0) {
    data.clusters.forEach(cluster => {
      const center = [cluster.centroid.lat, cluster.centroid.lng];
      bounds.push(center);

      // Draw Cluster Circle Polygon
      const circle = L.circle(center, {
        radius: cluster.radius_meters,
        color: cluster.color,
        fillColor: cluster.color,
        fillOpacity: 0.18,
        weight: 2,
        dashArray: '4, 4'
      });

      const clusterPopup = `
        <div style="font-family: 'Inter', sans-serif; font-size: 0.88rem; min-width: 200px;">
          <div style="font-weight: 800; font-size: 1rem; color: ${cluster.color}; margin-bottom: 0.3rem;">
            <i class="fa-solid fa-triangle-exclamation"></i> ${cluster.name}
          </div>
          <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.5rem;">
            DBSCAN Spatial Density Radius: ~${cluster.radius_meters}m
          </div>
          <ul style="list-style: none; padding: 0; margin: 0; font-size: 0.82rem; line-height: 1.6;">
            <li><strong>Total Reports:</strong> ${cluster.report_count}</li>
            <li><strong>High Priority:</strong> ${cluster.high_priority_count}</li>
            <li><strong>Awaiting Action:</strong> ${cluster.pending_count}</li>
            <li><strong>Severity:</strong> <span style="font-weight:700; color:${cluster.color};">${cluster.severity}</span></li>
          </ul>
        </div>
      `;
      circle.bindPopup(clusterPopup);
      clustersLayerGroup.addLayer(circle);

      // Render Clustered Report Markers
      cluster.reports.forEach(r => {
        addReportMarker(r, cluster.color, cluster.name);
        bounds.push([r.latitude, r.longitude]);
      });
    });
  }

  // 2. Render Isolated Noise Points (DBSCAN label -1)
  if (data.noise_points && data.noise_points.length > 0) {
    data.noise_points.forEach(r => {
      addReportMarker(r, '#64748b', 'Isolated Report (Noise Point)');
      bounds.push([r.latitude, r.longitude]);
    });
  }

  // Fit map bounds if markers exist
  if (bounds.length > 0) {
    hotspotMap.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
  }
}

function addReportMarker(report, clusterColor, clusterLabel) {
  const lat = report.latitude;
  const lng = report.longitude;

  // Custom Leaflet DivIcon
  const priorityColors = {
    'Urgent': '#ef4444',
    'High': '#ea580c',
    'Medium': '#f59e0b',
    'Low': '#10b981'
  };
  const pinColor = priorityColors[report.priority_level] || '#10b981';

  const customIcon = L.divIcon({
    className: 'custom-map-pin',
    html: `
      <div style="background-color: ${pinColor}; width: 26px; height: 26px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 2px solid #ffffff; box-shadow: 0 3px 6px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;">
        <i class="fa-solid fa-trash-can" style="transform: rotate(45deg); font-size: 10px; color: #ffffff;"></i>
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    popupAnchor: [0, -26]
  });

  const marker = L.marker([lat, lng], { icon: customIcon });

  const popupContent = `
    <div style="font-family: 'Inter', sans-serif; font-size: 0.88rem; min-width: 220px; line-height: 1.4;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
        <strong style="color: #0f172a; font-size: 0.95rem;">${report.complaint_id}</strong>
        ${getPriorityBadge(report.priority_level)}
      </div>
      <div style="margin-bottom: 0.4rem;">
        <span class="badge" style="background-color: #f1f5f9; color: #334155; font-size: 0.72rem;">${report.waste_category}</span>
        ${getStatusBadge(report.status)}
      </div>
      <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem;">
        <i class="fa-solid fa-location-dot" style="color: #10b981;"></i> ${report.address || `${lat.toFixed(4)}, ${lng.toFixed(4)}`}
      </p>
      <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.75rem;">
        <i class="fa-solid fa-layer-group"></i> ${clusterLabel}
      </div>
      <a href="/admin/reports?id=${report.complaint_id}" class="btn btn-primary btn-sm" style="width: 100%; text-align: center; color: white;">
        <i class="fa-solid fa-sliders"></i> Open in Report Management
      </a>
    </div>
  `;

  marker.bindPopup(popupContent);
  markersLayerGroup.addLayer(marker);

  // Store reference on report object for easy fly-to from list
  report._marker = marker;
}

function renderHotspotSidePanel(data) {
  const summary = data.summary || {};
  document.getElementById('summaryTotal').textContent = summary.total_reports || 0;
  document.getElementById('summaryClusters').textContent = summary.detected_clusters || 0;
  document.getElementById('summaryAwaiting').textContent = summary.awaiting_cleanup || 0;
  document.getElementById('summaryHighPriority').textContent = summary.high_priority_reports || 0;

  const clusterList = document.getElementById('detectedClustersList');
  if (!clusterList) return;

  if (!data.clusters || data.clusters.length === 0) {
    clusterList.innerHTML = `
      <div style="text-align: center; padding: 1.5rem; color: #94a3b8; font-size: 0.88rem;">
        No dense clusters detected with current DBSCAN parameters.
      </div>
    `;
    return;
  }

  clusterList.innerHTML = data.clusters.map(c => `
    <div class="hotspot-cluster-card" onclick="zoomToCluster(${c.centroid.lat}, ${c.centroid.lng}, 15)">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
        <strong style="font-size: 0.92rem; color: #0f172a;">${c.name}</strong>
        <span class="cluster-severity-pill" style="background-color: ${c.color}22; color: ${c.color}; border: 1px solid ${c.color};">
          ${c.severity}
        </span>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748b;">
        <span><i class="fa-solid fa-trash-can"></i> ${c.report_count} Reports</span>
        <span><i class="fa-solid fa-circle-exclamation" style="color: #ef4444;"></i> ${c.high_priority_count} Urgent</span>
        <span><i class="fa-solid fa-circle-nodes"></i> ~${c.radius_meters}m</span>
      </div>
    </div>
  `).join('');
}

window.zoomToCluster = function(lat, lng, zoomLevel = 16) {
  if (hotspotMap) {
    hotspotMap.flyTo([lat, lng], zoomLevel, { duration: 1 });
  }
};

function setupMapFilters() {
  const filters = ['filterCategory', 'filterStatus', 'filterPriority', 'filterEps'];
  filters.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', loadHotspotData);
  });

  const resetBtn = document.getElementById('resetMapFiltersBtn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      filters.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = id === 'filterEps' ? '700' : 'all';
      });
      loadHotspotData();
      if (hotspotMap) {
        hotspotMap.setView(DEFAULT_CENTER, 13);
      }
      showToast('Map filters reset to default.', 'info', 2000);
    });
  }
}
