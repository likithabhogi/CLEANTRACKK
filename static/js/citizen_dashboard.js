/**
 * CleanTrack AI - Citizen Dashboard Script
 */

let statusChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  loadCitizenDashboardData();
});

async function loadCitizenDashboardData() {
  const loadingOverlay = document.getElementById('dashboardLoading');
  if (loadingOverlay) loadingOverlay.style.display = 'block';

  try {
    // 1. Fetch Summary Stats & Activity
    const statsRes = await fetch('/api/citizen/stats');
    if (!statsRes.ok) throw new Error('Failed to fetch dashboard statistics.');
    const statsData = await statsRes.json();

    // 2. Fetch Recent Reports
    const reportsRes = await fetch('/api/citizen/reports');
    if (!reportsRes.ok) throw new Error('Failed to fetch citizen reports.');
    const reportsData = await reportsRes.json();

    renderSummaryKPIs(statsData.stats);
    renderStatusChart(statsData.status_distribution);
    renderRecentReportsTable(reportsData.reports);
    renderActivityFeed(statsData.recent_activities);

  } catch (err) {
    console.error(err);
    showToast(err.message || 'Error loading citizen dashboard.', 'error');
  } finally {
    if (loadingOverlay) loadingOverlay.style.display = 'none';
  }
}

function renderSummaryKPIs(stats) {
  document.getElementById('kpiTotal').textContent = stats.total || 0;
  document.getElementById('kpiPending').textContent = stats.pending || 0;
  document.getElementById('kpiInProgress').textContent = stats.in_progress || 0;
  document.getElementById('kpiResolved').textContent = stats.resolved || 0;
}

function renderStatusChart(statusDist) {
  const ctx = document.getElementById('citizenStatusChart');
  if (!ctx) return;

  const labels = ['Pending', 'Reviewed', 'Assigned', 'In Progress', 'Resolved'];
  const data = labels.map(l => statusDist[l] || 0);

  // If all zeroes, show placeholder
  const totalReports = data.reduce((a, b) => a + b, 0);

  if (statusChartInstance) {
    statusChartInstance.destroy();
  }

  if (totalReports === 0) {
    ctx.parentElement.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: #94a3b8;">
        <i class="fa-solid fa-chart-pie" style="font-size: 2.5rem; margin-bottom: 0.5rem; color: #cbd5e1;"></i>
        <p>No report data recorded yet.</p>
      </div>
    `;
    return;
  }

  statusChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: [
          '#f59e0b', // Pending (amber)
          '#8b5cf6', // Reviewed (purple)
          '#0284c7', // Assigned (sky)
          '#3b82f6', // In Progress (blue)
          '#10b981'  // Resolved (emerald)
        ],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 12,
            font: { size: 11, family: 'Inter' }
          }
        }
      },
      cutout: '70%'
    }
  });
}

function renderRecentReportsTable(reports) {
  const tbody = document.getElementById('recentReportsTableBody');
  const emptyState = document.getElementById('emptyReportsState');
  const tableWrapper = document.getElementById('reportsTableWrapper');

  if (!tbody) return;

  if (!reports || reports.length === 0) {
    if (tableWrapper) tableWrapper.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }

  if (tableWrapper) tableWrapper.style.display = 'block';
  if (emptyState) emptyState.style.display = 'none';

  // Take top 5 recent reports
  const displayReports = reports.slice(0, 5);

  tbody.innerHTML = displayReports.map(r => `
    <tr>
      <td style="font-weight: 700; color: #0284c7;">
        <a href="/my-reports?id=${r.complaint_id}" style="color: inherit;">
          ${r.complaint_id}
        </a>
      </td>
      <td>
        <span class="badge" style="background-color: #f1f5f9; color: #334155;">
          ${r.waste_category}
        </span>
      </td>
      <td style="font-size: 0.85rem; color: #64748b;">
        ${formatDate(r.created_at)}
      </td>
      <td style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.88rem;" title="${r.address || ''}">
        ${r.address || `Lat: ${r.latitude.toFixed(3)}, Lng: ${r.longitude.toFixed(3)}`}
      </td>
      <td>
        ${getStatusBadge(r.status)}
      </td>
      <td>
        <a href="/my-reports?id=${r.complaint_id}" class="btn btn-outline btn-sm">
          <i class="fa-solid fa-timeline"></i> Track
        </a>
      </td>
    </tr>
  `).join('');
}

function renderActivityFeed(activities) {
  const container = document.getElementById('citizenActivityFeed');
  if (!container) return;

  if (!activities || activities.length === 0) {
    container.innerHTML = `
      <p style="color: #94a3b8; font-size: 0.9rem; text-align: center; padding: 1.5rem 0;">
        No recent updates on your complaints yet.
      </p>
    `;
    return;
  }

  container.innerHTML = activities.map(act => `
    <div style="display: flex; gap: 0.85rem; padding: 0.75rem 0; border-bottom: 1px solid #f1f5f9;">
      <div style="width: 32px; height: 32px; border-radius: 50%; background-color: #ecfdf5; color: #10b981; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 0.85rem;">
        <i class="fa-solid fa-bell"></i>
      </div>
      <div style="flex: 1;">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
          <strong style="font-size: 0.88rem; color: #0f172a;">${act.complaint_id}</strong>
          <span style="font-size: 0.75rem; color: #94a3b8;">${formatDate(act.created_at)}</span>
        </div>
        <p style="font-size: 0.82rem; color: #475569; margin-top: 0.2rem;">
          ${act.notes || `Status transitioned to ${act.status}`}
        </p>
      </div>
    </div>
  `).join('');
}
