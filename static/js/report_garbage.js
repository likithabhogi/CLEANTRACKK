/**
 * CleanTrack AI - Report Garbage Script
 * Leaflet map pinpicker, AI classification inference, drag-and-drop upload
 */

let reportMap = null;
let reportMarker = null;
let selectedFile = null;

// Default city center (Bengaluru: 12.9716, 77.5946)
const DEFAULT_LAT = 12.9716;
const DEFAULT_LNG = 77.5946;

document.addEventListener('DOMContentLoaded', () => {
  initReportMap();
  setupImageUpload();
  setupGeolocation();
  setupFormSubmission();
});

/* ===================================================================
   Leaflet Map Initialization
   =================================================================== */

function initReportMap() {
  const mapElement = document.getElementById('reportMap');
  if (!mapElement) return;

  reportMap = L.map('reportMap').setView([DEFAULT_LAT, DEFAULT_LNG], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors | CleanTrack AI'
  }).addTo(reportMap);

  // Default Draggable Marker
  reportMarker = L.marker([DEFAULT_LAT, DEFAULT_LNG], {
    draggable: true
  }).addTo(reportMap);

  updateCoordinateInputs(DEFAULT_LAT, DEFAULT_LNG);

  // On marker drag end
  reportMarker.on('dragend', (e) => {
    const pos = e.target.getLatLng();
    updateCoordinateInputs(pos.lat, pos.lng);
  });

  // On map click
  reportMap.on('click', (e) => {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    reportMarker.setLatLng([lat, lng]);
    updateCoordinateInputs(lat, lng);
  });

  // Invalidate size after layout renders
  setTimeout(() => {
    reportMap.invalidateSize();
  }, 400);
}

function updateCoordinateInputs(lat, lng) {
  document.getElementById('reportLat').value = lat.toFixed(6);
  document.getElementById('reportLng').value = lng.toFixed(6);
  document.getElementById('coordDisplay').textContent = `Selected: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}

/* ===================================================================
   Geolocation Button
   =================================================================== */

function setupGeolocation() {
  const geoBtn = document.getElementById('useLocationBtn');
  if (!geoBtn) return;

  geoBtn.addEventListener('click', () => {
    if (!navigator.geolocation) {
      showToast('Geolocation is not supported by your browser.', 'error');
      return;
    }

    geoBtn.disabled = true;
    geoBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Detecting location...';

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;

        if (reportMap && reportMarker) {
          reportMap.setView([lat, lng], 16);
          reportMarker.setLatLng([lat, lng]);
          updateCoordinateInputs(lat, lng);
        }

        showToast('Location accurately pinpointed!', 'success');
        geoBtn.disabled = false;
        geoBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use My Current Location';
      },
      (err) => {
        let msg = 'Failed to retrieve your location.';
        if (err.code === 1) msg = 'Location permission denied by user.';
        else if (err.code === 2) msg = 'Location position unavailable.';
        else if (err.code === 3) msg = 'Location request timed out.';
        
        showToast(msg, 'warning');
        geoBtn.disabled = false;
        geoBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use My Current Location';
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  });
}

/* ===================================================================
   Image Upload & AI Waste Classification
   =================================================================== */

function setupImageUpload() {
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('reportImageInput');
  const previewBox = document.getElementById('imagePreviewContainer');
  const previewImg = document.getElementById('imagePreviewImg');
  const removeBtn = document.getElementById('removeImgBtn');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('click', () => fileInput.click());

  // Drag and Drop
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleImageSelection(files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleImageSelection(e.target.files[0]);
    }
  });

  removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = '';
    previewBox.style.display = 'none';
    previewImg.src = '';
    document.getElementById('aiDetectionCard').style.display = 'none';
    document.getElementById('aiPredictedCategoryInput').value = '';
    document.getElementById('aiConfidenceInput').value = '0';
  });
}

function handleImageSelection(file) {
  const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
  if (!allowed.includes(file.type)) {
    showToast('Please upload a valid image (JPG, JPEG, PNG, WEBP).', 'error');
    return;
  }

  if (file.size > 12 * 1024 * 1024) {
    showToast('Image size exceeds 12 MB limit.', 'error');
    return;
  }

  selectedFile = file;

  // Show client preview
  const previewBox = document.getElementById('imagePreviewContainer');
  const previewImg = document.getElementById('imagePreviewImg');
  const reader = new FileReader();

  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewBox.style.display = 'block';
  };
  reader.readAsDataURL(file);

  // Run AI Classification via backend API
  runAiClassification(file);
}

async function runAiClassification(file) {
  const aiCard = document.getElementById('aiDetectionCard');
  const aiSpinner = document.getElementById('aiSpinner');
  const aiResults = document.getElementById('aiResults');

  if (!aiCard) return;

  aiCard.style.display = 'block';
  aiSpinner.style.display = 'flex';
  aiResults.style.display = 'none';

  const formData = new FormData();
  formData.append('image', file);

  try {
    const res = await fetch('/api/ai/classify-waste', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'AI classification failed.');

    aiSpinner.style.display = 'none';
    aiResults.style.display = 'block';

    const predicted = data.predicted_category || 'Mixed Waste';
    const conf = data.confidence || 90.0;

    document.getElementById('aiPredictedName').textContent = predicted;
    document.getElementById('aiConfidenceScore').textContent = `${conf}% Confidence`;
    document.getElementById('aiConfidenceBar').style.width = `${conf}%`;
    document.getElementById('aiFeatureDetails').textContent = data.details || 'Feature visual match completed.';

    // Store in hidden inputs
    document.getElementById('aiPredictedCategoryInput').value = predicted;
    document.getElementById('aiConfidenceInput').value = conf;

    // Automatically set the category dropdown to the AI prediction
    const catSelect = document.getElementById('wasteCategorySelect');
    if (catSelect) {
      catSelect.value = predicted;
    }

    showToast(`AI detected: ${predicted} (${conf}%)`, 'info', 3000);

  } catch (err) {
    console.error(err);
    aiSpinner.style.display = 'none';
    aiCard.style.display = 'none';
    showToast('AI classification inference warning: please pick category manually.', 'warning');
  }
}

/* ===================================================================
   Form Submission
   =================================================================== */

function setupFormSubmission() {
  const form = document.getElementById('reportGarbageForm');
  const resetBtn = document.getElementById('resetFormBtn');

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      form.reset();
      selectedFile = null;
      document.getElementById('imagePreviewContainer').style.display = 'none';
      document.getElementById('aiDetectionCard').style.display = 'none';
      if (reportMarker) reportMarker.setLatLng([DEFAULT_LAT, DEFAULT_LNG]);
      if (reportMap) reportMap.setView([DEFAULT_LAT, DEFAULT_LNG], 13);
      updateCoordinateInputs(DEFAULT_LAT, DEFAULT_LNG);
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (!selectedFile) {
        showToast('Please upload a photo of the waste.', 'error');
        return;
      }

      const lat = parseFloat(document.getElementById('reportLat').value);
      const lng = parseFloat(document.getElementById('reportLng').value);
      const category = document.getElementById('wasteCategorySelect').value;
      const description = document.getElementById('reportDescription').value.trim();
      const address = document.getElementById('reportAddress').value.trim();
      const aiPred = document.getElementById('aiPredictedCategoryInput').value || category;
      const aiConf = document.getElementById('aiConfidenceInput').value || '90.0';

      if (!description) {
        showToast('Please enter a brief description of the waste.', 'error');
        return;
      }

      const submitBtn = document.getElementById('submitReportBtn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting Report...';

      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('latitude', lat);
      formData.append('longitude', lng);
      formData.append('waste_category', category);
      formData.append('description', description);
      formData.append('address', address);
      formData.append('ai_predicted_category', aiPred);
      formData.append('ai_confidence', aiConf);

      try {
        const res = await fetch('/api/reports', {
          method: 'POST',
          body: formData
        });

        const data = await res.json();

        if (res.ok && data.success) {
          // Show Success Modal
          document.getElementById('successComplaintId').textContent = data.complaint_id;
          document.getElementById('trackComplaintBtn').href = data.tracking_url;
          openModal('reportSuccessModal');

          // Reset Form
          form.reset();
          selectedFile = null;
          document.getElementById('imagePreviewContainer').style.display = 'none';
          document.getElementById('aiDetectionCard').style.display = 'none';
        } else {
          showToast(data.error || 'Failed to submit report.', 'error');
        }
      } catch (err) {
        showToast('Network error while submitting report.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Report';
      }
    });
  }
}
