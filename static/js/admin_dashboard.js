/**
 * CleanTrack AI - Administrator Dashboard Script
 * Integrates Chart.js (Line, Doughnut, Bar charts) & live data fetching
 */

let lineChart = null;
let doughnutChart = null;
let barChart = null;

document.addEventListener('DOMContentLoaded', () => {
  loadAdminDashboardData();

  // Status Filter in Recent Reports table
  const statusFilter = document.getElementById('recentStatusFilter');
  if (statusFilter) {
    statusFilter.addEventListener('change', () => {
      loadAdminDashboardData();
    });
  }
});

async function loadAdminDashboardData() {
  const loader = document.getElementById('adminDashboardLoading');
  if (loader) loader.style.display = 'block';

  try {
    const res = await fetch('/api/admin/stats');
    if (!res.ok) throw new Error('Failed to fetch administrator statistics.');
    const data = await res.json();

    renderAdminKPIs(data.kpi);
    renderCharts(data.trend, data.by_category, data.by_status);
    renderRecentReportsTable(data.recent_reports);
    renderAdminActivityFeed(data.activity_feed);

  } catch (err) {
    console.error(err);
    showToast(err.message || 'Error loading admin data.', 'error');
  } finally {
    if (loader) loader.style.display = 'none';
  }
}

function renderAdminKPIs(kpi) {
  document.getElementById('adminKpiTotal').textContent = kpi.total || 0;
  document.getElementById('adminKpiPending').textContent = kpi.pending || 0;
  document.getElementById('adminKpiHighPriority').textContent = kpi.high_priority || 0;
  document.getElementById('adminKpiInProgress').textContent = kpi.in_progress || 0;
  document.getElementById('adminKpiResolved').textContent = kpi.resolved || 0;
}

function renderCharts(trendData, categoryData, statusData) {
  // 1. Line Chart: Reports Trend Over Time
  const trendCtx = document.getElementById('trendLineChart');
  if (trendCtx) {
    if (lineChart) lineChart.destroy();

    const dates = trendData.length > 0 ? trendData.map(d => d.date) : ['Today'];
    const counts = trendData.length > 0 ? trendData.map(d => d.count) : [0];

    lineChart = new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{
          label: 'Complaints Logged',
          data: counts,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.35,
          pointBackgroundColor: '#047857',
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0, font: { family: 'Inter', size: 11 } },
            grid: { color: '#f1f5f9' }
          },
          x: {
            ticks: { font: { family: 'Inter', size: 11 } },
            grid: { display: false }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  // 2. Doughnut Chart: Reports by Category
  const catCtx = document.getElementById('categoryDoughnutChart');
  if (catCtx) {
    if (doughnutChart) doughnutChart.destroy();

    const catLabels = Object.keys(categoryData);
    const catCounts = Object.values(categoryData);

    doughnutChart = new Chart(catCtx, {
      type: 'doughnut',
      data: {
        labels: catLabels.length > 0 ? catLabels : ['No Data'],
        datasets: [{
          data: catCounts.length > 0 ? catCounts : [1],
          backgroundColor: [
            '#0284c7', // Plastic
            '#84cc16', // Organic
            '#f59e0b', // Mixed
            '#64748b', // Metal/Glass
            '#8b5cf6', // Paper
            '#ec4899'  // Other
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: {
          legend: {
            position: 'right',
            labels: { boxWidth: 12, font: { family: 'Inter', size: 11 } }
          }
        }
      }
    });
  }

  // 3. Bar Chart: Reports Count by Status
  const statusCtx = document.getElementById('statusBarChart');
  if (statusCtx) {
    if (barChart) barChart.destroy();

    const statusKeys = ['Pending', 'Reviewed', 'Assigned', 'In Progress', 'Resolved'];
    const statusCounts = statusKeys.map(k => statusData[k] || 0);

    barChart = new Chart(statusCtx, {
      type: 'bar',
      data: {
        labels: statusKeys,
        datasets: [{
          label: 'Total Reports',
          data: statusCounts,
          backgroundColor: [
            '#f59e0b',
            '#8b5cf6',
            '#0284c7',
            '#3b82f6',
            '#10b981'
          ],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0, font: { family: 'Inter', size: 11 } },
            grid: { color: '#f1f5f9' }
          },
          x: {
            ticks: { font: { family: 'Inter', size: 11 } },
            grid: { display: false }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
}

function renderRecentReportsTable(reports) {
  const tbody = document.getElementById('adminRecentReportsBody');
  if (!tbody) return;

  if (!reports || reports.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #94a3b8; padding: 2rem;">No recent reports found.</td></tr>`;
    return;
  }

  tbody.innerHTML = reports.map(r => `
    <tr>
      <td style="font-weight: 700; color: #0284c7;">
        <a href="/admin/reports?id=${r.complaint_id}" style="color: inherit;">
          ${r.complaint_id}
        </a>
      </td>
      <td>
        <span class="badge" style="background-color: #f1f5f9; color: #334155;">
          ${r.waste_category}
        </span>
      </td>
      <td style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.88rem;" title="${r.address || ''}">
        ${r.address}
      </td>
      <td>
        ${getPriorityBadge(r.priority_level)}
      </td>
      <td style="font-size: 0.85rem; color: #64748b;">
        ${formatDate(r.created_at)}
      </td>
      <td>
        ${getStatusBadge(r.status)}
      </td>
      <td>
        <a href="/admin/reports?id=${r.complaint_id}" class="btn btn-outline btn-sm">
          <i class="fa-solid fa-pen-to-square"></i> Review
        </a>
      </td>
    </tr>
  `).join('');
}

function renderAdminActivityFeed(feed) {
  const container = document.getElementById('adminActivityFeed');
  if (!container) return;

  if (!feed || feed.length === 0) {
    container.innerHTML = `<p style="text-align: center; color: #94a3b8; padding: 1.5rem 0;">No recent activity records.</p>`;
    return;
  }

  container.innerHTML = feed.map(item => `
    <div style="display: flex; gap: 0.85rem; padding: 0.75rem 0; border-bottom: 1px solid #f1f5f9;">
      <div style="width: 32px; height: 32px; border-radius: 50%; background-color: #e0f2fe; color: #0284c7; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 0.85rem;">
        <i class="fa-solid fa-clock-rotate-left"></i>
      </div>
      <div style="flex: 1;">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
          <strong style="font-size: 0.88rem; color: #0f172a;">${item.complaint_id}</strong>
          <span style="font-size: 0.75rem; color: #94a3b8;">${formatDate(item.created_at)}</span>
        </div>
        <p style="font-size: 0.82rem; color: #475569; margin-top: 0.2rem;">
          <span style="font-weight: 600;">${item.changed_by}:</span> ${item.notes || `Status changed to ${item.status}`}
        </p>
      </div>
    </div>
  `).join('');
}
