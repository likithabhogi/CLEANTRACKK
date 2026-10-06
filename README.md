# CleanTrack AI – AI-Powered Smart Waste Management System

CleanTrack AI is a modern, responsive, and data-driven civic intelligence web application designed to connect citizens with municipal sanitation teams in real time. It automates waste identification using computer vision heuristics, clusters reports geographically using Scikit-Learn DBSCAN, calculates explainable priority scores, and enables municipal authorities to dispatch cleanup squads with verified photographic proof.

---

## 🌟 8 Included Pages

1. **Page 1: Home Page (`/`)**
   - Modern, eco-friendly landing page with green/white/light-grey environmental aesthetic.
   - Sticky navigation bar with CleanTrack AI logo, anchor links, and authentication routing.
   - Hero banner with **"Making Our Cities Cleaner with AI"**, dual action buttons (*Report Garbage* and *Explore Dashboard*), and smart city vector illustration.
   - 4 Core Feature cards: AI Waste Detection, Smart Hotspot Mapping, Real-Time Tracking, and Cleanup Management.
   - 5-Step How-It-Works interactive workflow.
   - Municipal impact statistics clearly marked as demonstrated pilot metrics.
   - Purpose & mission about section, and municipal footer with contact information.

2. **Page 2: Login and Registration (`/login`, `/register`)**
   - Professional tabbed authentication card matching the CleanTrack AI design system.
   - Password visibility show/hide toggle, Remember Me support, and demo recovery triggers.
   - Role-based registration for **Citizen** and **Administrator**.
   - Werkzeug secure password hashing (`generate_password_hash`, `check_password_hash`).
   - One-click demo credentials loader buttons for instant test evaluation.

3. **Page 3: Citizen Dashboard (`/citizen/dashboard`)**
   - Responsive sidebar navigation and personalized welcome header.
   - 4 Dynamic KPI summary cards: *Total Reports*, *Pending Review*, *Cleanup In Progress*, and *Verified Resolved*.
   - Prominent *Report New Garbage* action button.
   - Recent Reports table with live status badges and direct complaint tracking links.
   - Doughnut status distribution chart rendered with **Chart.js**.
   - Live activity notification feed and friendly empty states.

4. **Page 4: Report Garbage (`/report`)**
   - Drag-and-drop image upload zone supporting JPG, JPEG, PNG, and WEBP.
   - Instant client-side preview with remove button.
   - Automated AI Waste Classification (`/api/ai/classify-waste`) with confidence score bar and feature details.
   - Citizen category confirmation and override dropdown (Plastic, Paper/Cardboard, Organic, Metal/Glass, Mixed Waste, Other).
   - Browser geolocation (*Use My Current Location*) and interactive **Leaflet map pinpicker** with live coordinates.
   - Submission modal displaying unique complaint tracking ID (e.g. `CT-2026-XXXX`).

5. **Page 5: My Reports & Tracking (`/my-reports`)**
   - Real-time search by complaint ID or location.
   - Filter pills: *All*, *Pending*, *Reviewed*, *Assigned*, *In Progress*, and *Resolved*.
   - Detailed modal tracking view featuring an interactive **5-stage progress pipeline**:
     1. Report Submitted → 2. Report Reviewed → 3. Cleanup Assigned → 4. Cleanup In Progress → 5. Resolved.
   - Split before-and-after photo comparison (Citizen Photo vs. Municipal Squad Cleanup Proof).
   - Official municipal administration logs and timestamp audit history.

6. **Page 6: Admin Dashboard (`/admin/dashboard`)**
   - Municipal command center with role-restricted access.
   - 5 Summary metric cards including *High Priority* SLA counter.
   - 3 Interactive **Chart.js** visualizations:
     1. Complaints Trend Over Time (Line Chart)
     2. Reports by Waste Category (Doughnut Chart)
     3. Report Counts by Operational Status (Bar Chart)
   - Recent incidents table with priority level badges and quick triage actions.
   - Live municipal dispatch audit feed.

7. **Page 7: Garbage Hotspot Map (`/admin/hotspots`)**
   - Geographic monitoring dashboard powered by **Leaflet.js** and **OpenStreetMap**.
   - Spatial clustering executed on the backend using **Scikit-Learn DBSCAN (`sklearn.cluster.DBSCAN`)**.
   - Radius circles and color-coded severity rings indicating cluster density (Critical, Moderate, Low).
   - Isolated reports displayed as distinct noise points (DBSCAN label -1).
   - Multi-filter controls: Category, Status, Priority, and Cluster Neighborhood Radius (Epsilon: 400m, 700m, 1200m).
   - Side panel with real-time cluster counts and clickable hotspot list that flies the map camera to the zone.

8. **Page 8: Report Management and Cleanup (`/admin/reports`)**
   - Comprehensive triage console for municipal administrators.
   - Search and multi-criteria filters for status, category, and priority.
   - Deep review drawer with mini Leaflet location map, citizen description, and AI vision inference output.
   - **Explainable Priority Scoring Engine (1 - 100)**: Displays transparent breakdown of contributing factors (*Waste Type Hazard*, *Complaint Age Escalation*, *Public Sensitivity Keywords*, and *Hotspot Cluster Proximity*).
   - Municipal team allocation dropdown with live workload counters.
   - Status workflow transitions and upload field for after-cleanup proof photos.

---

## 🔑 Demo Credentials (Test Accounts)

| Role | Email | Password | Pre-seeded Features |
|---|---|---|---|
| **Citizen** | `citizen@cleantrack.ai` | `Citizen123!` | Active reports, progress timelines, before/after proof images |
| **Administrator** | `admin@cleantrack.ai` | `Admin123!` | Hotspot map, DBSCAN clustering, triage dispatch, squad allocation |

*Note: You can also click the "Citizen Demo" or "Admin Demo" buttons on the Login page to auto-fill these credentials.*

---

## 🚀 How to Run the Application

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Initialize / Seed the Database (Optional - Runs automatically if DB is empty)
```bash
python seed_data.py
```

### 3. Launch Flask Server
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```
