/**
 * CleanTrack AI - Report Management and Cleanup Script
 * Admin Triage, Explainable Priority Breakdown, Team Assignment, and Proof Upload
 */

let allAdminReports = [];
let availableTeams = [];
let activeReportForModal = null;
let triageMiniMap = null;
let triageMiniMarker = null;

document.addEventListener('DOMContentLoaded', () => {
  loadAdminReports();
  loadCleanupTeams();
  setupFilters();
  setupTriageForm();
});

async function loadCleanupTeams() {
  try {
    const res = await fetch('/api/admin/teams');
    if (res.ok) {
      const data = await res.json();
      availableTeams = data.teams || [];
      populateTeamDropdown();
    }
  } catch (err) {
    console.error('Failed to load cleanup teams:', err);
  }
}

function populateTeamDropdown() {
  const select = document.getElementById('triageTeamSelect');
  if (!select) return;

  select.innerHTML = `
    <option value="">-- No Team Assigned --</option>
    ${availableTeams.map(t => `
      <option value="${t.id}">
        ${t.team_name} (${t.ward}) - [${t.status}, Active: ${t.current_load}]
      </option>
    `).join('')}
  `;
}

async function loadAdminReports() {
  const loader = document.getElementById('manageReportsLoader');
  if (loader) loader.style.display = 'block';

  const status = document.getElementById('filterStatus') ? document.getElementById('filterStatus').value : 'all';
  const category = document.getElementById('filterCategory') ? document.getElementById('filterCategory').value : 'all';
  const priority = document.getElementById('filterPriority') ? document.getElementById('filterPriority').value : 'all';
  const search = document.getElementById('reportSearch') ? document.getElementById('reportSearch').value.trim() : '';

  const url = `/api/admin/reports?status=${status}&category=${category}&priority=${priority}&search=${encodeURIComponent(search)}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to retrieve reports.');
    const data = await res.json();

    allAdminReports = data.reports || [];
    renderReportsTable(allAdminReports);

    // If URL has ?id=COMPLAINT_ID, open modal
    const urlParams = new URLSearchParams(window.location.search);
    const complaintId = urlParams.get('id');
    if (complaintId) {
      openReportTriageModal(complaintId);
    }

  } catch (err) {
    console.error(err);
    showToast(err.message || 'Error loading reports.', 'error');
  } finally {
    if (loader) loader.style.display = 'none';
  }
}

function setupFilters() {
  const inputs = ['filterStatus', 'filterCategory', 'filterPriority'];
  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', loadAdminReports);
  });

  const search = document.getElementById('reportSearch');
  if (search) {
    let debounceTimer;
    search.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(loadAdminReports, 300);
    });
  }

  const resetBtn = document.getElementById('resetFiltersBtn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = 'all';
      });
      if (search) search.value = '';
      loadAdminReports();
      showToast('Filters cleared.', 'info', 2000);
    });
  }
}

function renderReportsTable(reports) {
  const tbody = document.getElementById('manageReportsTableBody');
  if (!tbody) return;

  if (!reports || reports.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: #94a3b8; padding: 2.5rem;">No reports match the filter criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = reports.map(r => `
    <tr>
      <td style="font-weight: 700; color: #0284c7;">
        ${r.complaint_id}
      </td>
      <td>
        <img src="${r.image_url}" alt="Report" 
             style="width: 50px; height: 50px; object-fit: cover; border-radius: var(--radius-sm); border: 1px solid var(--border-light);" />
      </td>
      <td>
        <span class="badge" style="background-color: #f1f5f9; color: #334155;">
          ${r.waste_category}
        </span>
      </td>
      <td style="max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.85rem;" title="${r.address || ''}">
        ${r.address}
      </td>
      <td>
        <div style="font-size: 0.82rem; font-weight: 600; color: #0f172a;">${r.ai_predicted_category || 'N/A'}</div>
        <div style="font-size: 0.75rem; color: #10b981;">${r.ai_confidence ? r.ai_confidence + '%' : ''}</div>
      </td>
      <td>
        <div style="display: flex; align-items: center; gap: 0.4rem;">
          ${getPriorityBadge(r.priority_level)}
          <span style="font-size: 0.8rem; font-weight: 700; color: #475569;">(${r.priority_score})</span>
        </div>
      </td>
      <td style="font-size: 0.82rem; color: #64748b;">
        ${formatDate(r.created_at)}
      </td>
      <td>
        ${getStatusBadge(r.status)}
      </td>
      <td>
        <button class="btn btn-primary btn-sm" onclick="openReportTriageModal('${r.complaint_id}')">
          <i class="fa-solid fa-gear"></i> Triage
        </button>
      </td>
    </tr>
  `).join('');
}

async function openReportTriageModal(complaintId) {
  try {
    const res = await fetch(`/api/reports/${complaintId}`);
    if (!res.ok) throw new Error('Could not fetch report details.');
    const data = await res.json();

    const report = data.report;
    const history = data.history;
    activeReportForModal = report;

    document.getElementById('triageComplaintId').textContent = report.complaint_id;
    document.getElementById('triageReporter').textContent = `${report.reporter_name} (${report.reporter_email || 'No Email'})`;
    document.getElementById('triageDate').textContent = formatDate(report.created_at);
    document.getElementById('triageCategory').textContent = report.waste_category;
    document.getElementById('triageAiDetection').textContent = `${report.ai_predicted_category || 'N/A'} (${report.ai_confidence || 0}% Confidence)`;
    document.getElementById('triageAddress').textContent = report.address;
    document.getElementById('triageDescription').textContent = report.description || 'No description provided.';
    document.getElementById('triageOriginalImg').src = report.image_url;

    // After Image Preview
    const afterImg = document.getElementById('triageAfterImg');
    const afterPlaceholder = document.getElementById('triageAfterPlaceholder');
    if (report.after_image_url) {
      afterImg.src = report.after_image_url;
      afterImg.style.display = 'block';
      afterPlaceholder.style.display = 'none';
    } else {
      afterImg.style.display = 'none';
      afterPlaceholder.style.display = 'flex';
    }

    // Populate Status & Team
    document.getElementById('triageStatusSelect').value = report.status;
    document.getElementById('triageTeamSelect').value = report.assigned_team_id || '';
    document.getElementById('triageAdminNotes').value = report.admin_notes || '';

    // Render Explainable Priority Score Breakdown
    renderPriorityFactors(report.priority_score, report.priority_level, report.priority_factors);

    // Render Mini Map
    initTriageMiniMap(report.latitude, report.longitude);

    // Render History Timeline
    renderTriageHistoryLog(history);

    openModal('reportTriageModal');

  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderPriorityFactors(score, level, factors) {
  document.getElementById('triagePriorityScoreDisplay').textContent = score || 50;
  document.getElementById('triagePriorityBadgeDisplay').innerHTML = getPriorityBadge(level);

  const container = document.getElementById('triageFactorsList');
  if (!container) return;

  if (!factors || factors.length === 0) {
    container.innerHTML = `<li style="font-size: 0.82rem; color: #94a3b8;">Standard municipal baseline score applied.</li>`;
    return;
  }

  container.innerHTML = factors.map(f => `
    <li class="factor-item">
      <div>
        <strong style="color: #0f172a;">${f.factor}:</strong>
        <span style="color: #64748b;"> ${f.detail}</span>
      </div>
      <span style="font-weight: 700; color: ${f.points > 0 ? '#10b981' : '#94a3b8'};">
        +${f.points} pts
      </span>
    </li>
  `).join('');
}

function initTriageMiniMap(lat, lng) {
  const mapElem = document.getElementById('triageMiniMap');
  if (!mapElem) return;

  if (!triageMiniMap) {
    triageMiniMap = L.map('triageMiniMap').setView([lat, lng], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }).addTo(triageMiniMap);
    triageMiniMarker = L.marker([lat, lng]).addTo(triageMiniMap);
  } else {
    triageMiniMap.setView([lat, lng], 15);
    triageMiniMarker.setLatLng([lat, lng]);
  }

  setTimeout(() => {
    triageMiniMap.invalidateSize();
  }, 350);
}

function renderTriageHistoryLog(history) {
  const container = document.getElementById('triageAuditHistory');
  if (!container) return;

  if (!history || history.length === 0) {
    container.innerHTML = `<p style="font-size: 0.85rem; color: #94a3b8;">No prior audit history.</p>`;
    return;
  }

  container.innerHTML = history.map(h => `
    <div style="font-size: 0.82rem; padding: 0.4rem 0; border-bottom: 1px dashed #e2e8f0;">
      <div style="display: flex; justify-content: space-between;">
        <strong style="color: #0f172a;">${h.status}</strong>
        <span style="color: #94a3b8;">${formatDate(h.created_at)}</span>
      </div>
      <div style="color: #64748b; margin-top: 0.15rem;">
        <em>${h.changed_by}:</em> ${h.notes || 'Status updated'}
      </div>
    </div>
  `).join('');
}

function setupTriageForm() {
  const form = document.getElementById('triageUpdateForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!activeReportForModal) return;

    const saveBtn = document.getElementById('triageSaveBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving Updates...';

    const complaintId = activeReportForModal.complaint_id;
    const newStatus = document.getElementById('triageStatusSelect').value;
    const teamId = document.getElementById('triageTeamSelect').value;
    const notes = document.getElementById('triageAdminNotes').value.trim();
    const proofFile = document.getElementById('triageProofFileInput').files[0];

    const formData = new FormData();
    formData.append('status', newStatus);
    formData.append('assigned_team_id', teamId);
    formData.append('admin_notes', notes);
    if (proofFile) {
      formData.append('after_image', proofFile);
    }

    try {
      const res = await fetch(`/api/admin/reports/${complaintId}/update`, {
        method: 'POST',
        body: formData
      });

      const data = await res.json();

      if (res.ok && data.success) {
        showToast(data.message, 'success');
        closeModal('reportTriageModal');
        // Refresh table and teams
        loadAdminReports();
        loadCleanupTeams();
      } else {
        showToast(data.error || 'Failed to update report.', 'error');
      }
    } catch (err) {
      showToast('Network error while saving changes.', 'error');
    } finally {
      saveBtn.disabled = false;
      saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save &amp; Dispatch Changes';
    }
  });
}
