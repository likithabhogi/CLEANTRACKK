/**
 * CleanTrack AI - My Reports and Tracking Script
 */

let allCitizenReports = [];

document.addEventListener('DOMContentLoaded', () => {
  loadCitizenReports();
  setupFiltersAndSearch();

  // Refresh Button
  const refreshBtn = document.getElementById('refreshReportsBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      refreshBtn.classList.add('fa-spin');
      loadCitizenReports().finally(() => {
        setTimeout(() => refreshBtn.classList.remove('fa-spin'), 600);
      });
    });
  }
});

async function loadCitizenReports() {
  const loadingIndicator = document.getElementById('reportsLoading');
  if (loadingIndicator) loadingIndicator.style.display = 'block';

  try {
    const res = await fetch('/api/citizen/reports');
    if (!res.ok) throw new Error('Failed to load your reports.');
    const data = await res.json();

    allCitizenReports = data.reports || [];
    renderReportsList(allCitizenReports);

    // Check if URL has ?id=COMPLAINT_ID to auto open tracking modal
    const urlParams = new URLSearchParams(window.location.search);
    const complaintIdParam = urlParams.get('id');
    if (complaintIdParam) {
      openReportTrackingModal(complaintIdParam);
    }
  } catch (err) {
    console.error(err);
    showToast(err.message || 'Error loading reports.', 'error');
  } finally {
    if (loadingIndicator) loadingIndicator.style.display = 'none';
  }
}

function setupFiltersAndSearch() {
  const searchInput = document.getElementById('reportSearchInput');
  const filterPills = document.querySelectorAll('.filter-pill');

  let activeStatus = 'all';

  function applyFilters() {
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

    const filtered = allCitizenReports.filter(r => {
      const matchesStatus = (activeStatus === 'all') || (r.status.toLowerCase() === activeStatus.toLowerCase());
      const matchesSearch = !query || 
        r.complaint_id.toLowerCase().includes(query) ||
        (r.address && r.address.toLowerCase().includes(query)) ||
        (r.waste_category && r.waste_category.toLowerCase().includes(query));

      return matchesStatus && matchesSearch;
    });

    renderReportsList(filtered);
  }

  if (searchInput) {
    searchInput.addEventListener('input', applyFilters);
  }

  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeStatus = pill.getAttribute('data-status');
      applyFilters();
    });
  });
}

function renderReportsList(reports) {
  const container = document.getElementById('reportsListContainer');
  const emptyState = document.getElementById('noReportsFound');

  if (!container) return;

  if (!reports || reports.length === 0) {
    container.innerHTML = '';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';

  container.innerHTML = reports.map(r => `
    <div class="content-card" style="margin-bottom: 1.25rem; transition: transform 0.2s ease;">
      <div style="display: flex; gap: 1.25rem; align-items: flex-start; flex-wrap: wrap;">
        <img src="${r.image_url}" alt="Report Image" 
             style="width: 110px; height: 95px; object-fit: cover; border-radius: var(--radius-md); border: 1px solid var(--border-light); flex-shrink: 0;" />
        
        <div style="flex: 1; min-width: 240px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem; flex-wrap: wrap; gap: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
              <span style="font-weight: 800; font-size: 1.1rem; color: #0f172a;">${r.complaint_id}</span>
              <span class="badge" style="background-color: #f1f5f9; color: #334155;">${r.waste_category}</span>
            </div>
            ${getStatusBadge(r.status)}
          </div>

          <p style="font-size: 0.88rem; color: #64748b; margin-bottom: 0.5rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
            ${r.description || 'No description provided.'}
          </p>

          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; font-size: 0.8rem; color: #94a3b8;">
            <span><i class="fa-solid fa-location-dot" style="color: #10b981;"></i> ${r.address || 'Location Coordinates Recorded'}</span>
            <span><i class="fa-regular fa-calendar"></i> ${formatDate(r.created_at)}</span>
          </div>
        </div>

        <div style="align-self: center;">
          <button class="btn btn-primary btn-sm" onclick="openReportTrackingModal('${r.complaint_id}')">
            <i class="fa-solid fa-magnifying-glass-location"></i> View Details &amp; Tracking
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

async function openReportTrackingModal(complaintId) {
  try {
    const res = await fetch(`/api/reports/${complaintId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch tracking details.');

    const report = data.report;
    const timeline = data.timeline;

    document.getElementById('modalComplaintId').textContent = report.complaint_id;
    document.getElementById('modalCategoryBadge').textContent = report.waste_category;
    document.getElementById('modalStatusBadge').innerHTML = getStatusBadge(report.status);
    document.getElementById('modalAddress').textContent = report.address;
    document.getElementById('modalReportDate').textContent = formatDate(report.created_at);
    document.getElementById('modalDescription').textContent = report.description || 'N/A';
    document.getElementById('modalOriginalImage').src = report.image_url;

    // After Cleanup Proof
    const afterBox = document.getElementById('modalAfterImageBox');
    const afterImg = document.getElementById('modalAfterImage');
    const afterPlaceholder = document.getElementById('modalAfterPlaceholder');

    if (report.after_image_url) {
      afterImg.src = report.after_image_url;
      afterImg.style.display = 'block';
      afterPlaceholder.style.display = 'none';
    } else {
      afterImg.style.display = 'none';
      afterPlaceholder.style.display = 'flex';
    }

    // Render 5-Stage Timeline
    renderTimelineStepper(timeline);

    // Admin notes
    const notesBox = document.getElementById('modalAdminNotes');
    notesBox.textContent = report.admin_notes || 'No administrative instructions recorded yet.';

    openModal('reportTrackingModal');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderTimelineStepper(timeline) {
  const container = document.getElementById('modalTimelineContainer');
  if (!container) return;

  const stepIcons = {
    'Pending': 'fa-paper-plane',
    'Reviewed': 'fa-clipboard-check',
    'Assigned': 'fa-people-group',
    'In Progress': 'fa-truck-moving',
    'Resolved': 'fa-circle-check'
  };

  container.innerHTML = timeline.map(step => {
    let stateClass = '';
    if (step.is_current) stateClass = 'active';
    else if (step.is_completed) stateClass = 'completed';

    const icon = stepIcons[step.stage] || 'fa-circle';

    return `
      <div class="timeline-step ${stateClass}">
        <div class="step-circle">
          <i class="fa-solid ${icon}"></i>
        </div>
        <div class="step-label">${step.title}</div>
        <div class="step-time">${step.timestamp ? formatDate(step.timestamp) : 'Pending'}</div>
      </div>
    `;
  }).join('');
}
