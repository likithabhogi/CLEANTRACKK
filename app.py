import os
import uuid
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from database import get_db, init_db
from services.ai_service import analyze_waste_image, CATEGORIES
from services.clustering_service import run_dbscan_clustering
from services.priority_service import calculate_priority_score

app = Flask(__name__)
app.config.from_object(Config)

# Helper: Allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Auth Decorators
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({"error": "Authentication required. Please log in."}), 401
                return redirect(url_for('login_page', next=request.path))
            
            if role and session.get('role') != role:
                if request.path.startswith('/api/'):
                    return jsonify({"error": f"Access denied. '{role}' role required."}), 403
                # If citizen attempts admin page, redirect to citizen dashboard
                if session.get('role') == 'citizen':
                    return redirect(url_for('citizen_dashboard_page'))
                return redirect(url_for('home_page'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Context Processor for User session in templates
@app.context_processor
def inject_user():
    return {
        'current_user': {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email'),
            'role': session.get('role')
        } if 'user_id' in session else None,
        'year': datetime.now().year
    }

# ==========================================
# PAGE ROUTES (All 8 Pages)
# ==========================================

@app.route('/')
def home_page():
    """Page 1: Home Landing Page"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Page 2: Login and Registration Page"""
    # If already logged in, redirect to respective dashboard
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard_page'))
        return redirect(url_for('citizen_dashboard_page'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Convenience redirect to registration tab on Page 2"""
    return redirect(url_for('login_page', tab='register'))

@app.route('/citizen/dashboard')
@login_required(role='citizen')
def citizen_dashboard_page():
    """Page 3: Citizen Dashboard"""
    return render_template('citizen_dashboard.html')

@app.route('/report')
@login_required(role='citizen')
def report_garbage_page():
    """Page 4: Report Garbage"""
    return render_template('report_garbage.html')

@app.route('/my-reports')
@login_required(role='citizen')
def my_reports_page():
    """Page 5: My Reports and Tracking"""
    return render_template('my_reports.html')

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard_page():
    """Page 6: Admin Dashboard"""
    return render_template('admin_dashboard.html')

@app.route('/admin/hotspots')
@login_required(role='admin')
def hotspot_map_page():
    """Page 7: Garbage Hotspot Map"""
    return render_template('hotspot_map.html')

@app.route('/admin/reports')
@login_required(role='admin')
def manage_reports_page():
    """Page 8: Report Management and Cleanup"""
    return render_template('manage_reports.html')

@app.route('/logout')
def logout_route():
    session.clear()
    return redirect(url_for('home_page'))

# ==========================================
# AUTHENTICATION REST APIS
# ==========================================

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    role = data.get('role', 'citizen').strip().lower()

    if not full_name or not email or not password:
        return jsonify({"error": "Full name, email, and password are required."}), 400

    if '@' not in email or '.' not in email:
        return jsonify({"error": "Please provide a valid email address."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400

    if role not in ['citizen', 'admin']:
        role = 'citizen'

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "An account with this email already exists."}), 409

    hashed_pw = generate_password_hash(password)
    try:
        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, (full_name, email, phone, hashed_pw, role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # Automatically log in the registered user
        session['user_id'] = user_id
        session['user_name'] = full_name
        session['user_email'] = email
        session['role'] = role

        redirect_url = '/admin/dashboard' if role == 'admin' else '/citizen/dashboard'
        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "redirect": redirect_url,
            "user": {"id": user_id, "name": full_name, "email": email, "role": role}
        }), 201

    except Exception as e:
        conn.close()
        return jsonify({"error": f"Failed to register account: {str(e)}"}), 500

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    remember = data.get('remember', False)

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid email or password. Please try again."}), 401

    session.permanent = bool(remember)
    session['user_id'] = user['id']
    session['user_name'] = user['full_name']
    session['user_email'] = user['email']
    session['role'] = user['role']

    redirect_url = '/admin/dashboard' if user['role'] == 'admin' else '/citizen/dashboard'
    return jsonify({
        "success": True,
        "message": f"Welcome back, {user['full_name']}!",
        "redirect": redirect_url,
        "user": {
            "id": user['id'],
            "name": user['full_name'],
            "email": user['email'],
            "role": user['role']
        }
    }), 200

@app.route('/api/auth/me', methods=['GET'])
def api_auth_me():
    if 'user_id' not in session:
        return jsonify({"authenticated": False, "user": None}), 200
    
    return jsonify({
        "authenticated": True,
        "user": {
            "id": session.get('user_id'),
            "name": session.get('user_name'),
            "email": session.get('user_email'),
            "role": session.get('role')
        }
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully.", "redirect": "/"}), 200

# ==========================================
# AI CLASSIFICATION REST API
# ==========================================

@app.route('/api/ai/classify-waste', methods=['POST'])
def api_classify_waste():
    """
    Accepts an uploaded image file and returns AI predicted waste category,
    confidence score, and feature analysis details.
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided."}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not supported. Please upload JPG, PNG, or WEBP."}), 400

    # Save to temp location in uploads
    ext = file.filename.rsplit('.', 1)[1].lower()
    temp_filename = f"ai_temp_{uuid.uuid4().hex[:10]}.{ext}"
    temp_path = os.path.join(Config.UPLOAD_FOLDER, temp_filename)
    file.save(temp_path)

    # Run AI inference
    result = analyze_waste_image(temp_path)

    return jsonify(result), 200

# ==========================================
# REPORT SUBMISSION & CITIZEN REST APIS
# ==========================================

@app.route('/api/reports', methods=['POST'])
@login_required(role='citizen')
def api_create_report():
    """
    Citizen reports waste with image, coordinates, category, and description.
    Computes priority and saves to SQLite.
    """
    if 'image' not in request.files:
        return jsonify({"error": "Waste image is required."}), 400

    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Valid image file (JPG, PNG, WEBP) is required."}), 400

    waste_category = request.form.get('waste_category', 'Mixed Waste').strip()
    ai_predicted = request.form.get('ai_predicted_category', waste_category)
    ai_confidence = float(request.form.get('ai_confidence', 90.0))
    description = request.form.get('description', '').strip()
    address = request.form.get('address', '').strip()
    
    try:
        lat = float(request.form.get('latitude', 0))
        lng = float(request.form.get('longitude', 0))
    except ValueError:
        return jsonify({"error": "Valid latitude and longitude coordinates are required."}), 400

    if lat == 0 and lng == 0:
        return jsonify({"error": "Please pick a valid location on the map."}), 400

    # Save uploaded image
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"report_{uuid.uuid4().hex[:12]}.{ext}"
    file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
    file.save(file_path)
    image_url = f"/static/uploads/{unique_filename}"

    # Generate unique complaint ID: CT-YEAR-RANDOM
    complaint_id = f"CT-{datetime.now().year}-{uuid.uuid4().hex[:5].upper()}"

    # Compute Initial Priority Score
    priority_info = calculate_priority_score(
        waste_category=waste_category,
        description=description,
        address=address,
        hours_elapsed=0,
        is_in_cluster=False
    )

    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
        INSERT INTO reports (
            complaint_id, user_id, image_url, waste_category,
            ai_predicted_category, ai_confidence, description,
            latitude, longitude, address, priority_score,
            priority_level, priority_factors, status,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
    """, (
        complaint_id, session['user_id'], image_url, waste_category,
        ai_predicted, ai_confidence, description,
        lat, lng, address or f"Lat: {lat:.4f}, Lng: {lng:.4f}",
        priority_info['score'], priority_info['level'],
        json.dumps(priority_info['factors']),
        now_str, now_str
    ))

    report_id = cursor.lastrowid

    # Add initial audit history record
    cursor.execute("""
        INSERT INTO report_history (report_id, status, changed_by, notes, created_at)
        VALUES (?, 'Pending', ?, 'Report submitted by citizen with AI waste verification', ?)
    """, (report_id, session.get('user_name', 'Citizen'), now_str))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Waste report submitted successfully!",
        "complaint_id": complaint_id,
        "tracking_url": f"/my-reports?id={complaint_id}"
    }), 201

@app.route('/api/citizen/reports', methods=['GET'])
@login_required(role='citizen')
def api_citizen_reports():
    """Returns reports belonging solely to the logged-in citizen with search & filter."""
    user_id = session['user_id']
    status_filter = request.args.get('status', 'all').strip().lower()
    search = request.args.get('search', '').strip().lower()

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT r.*, t.team_name, t.lead_name 
        FROM reports r 
        LEFT JOIN cleanup_teams t ON r.assigned_team_id = t.id
        WHERE r.user_id = ?
    """
    params = [user_id]

    if status_filter and status_filter != 'all':
        query += " AND LOWER(r.status) = ?"
        params.append(status_filter)

    if search:
        query += " AND (LOWER(r.complaint_id) LIKE ? OR LOWER(r.address) LIKE ? OR LOWER(r.waste_category) LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    query += " ORDER BY r.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    reports = [dict(row) for row in rows]
    return jsonify({"reports": reports, "count": len(reports)}), 200

@app.route('/api/citizen/stats', methods=['GET'])
@login_required(role='citizen')
def api_citizen_stats():
    """Returns citizen KPI summary metrics and status distribution."""
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status IN ('Reviewed', 'Assigned', 'In Progress') THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved
        FROM reports WHERE user_id = ?
    """, (user_id,))
    counts = dict(cursor.fetchone())

    # Reports by status for Chart.js
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM reports WHERE user_id = ? 
        GROUP BY status
    """, (user_id,))
    status_dist = {row['status']: row['count'] for row in cursor.fetchall()}

    # Recent report timeline activities
    cursor.execute("""
        SELECT h.*, r.complaint_id, r.waste_category
        FROM report_history h
        JOIN reports r ON h.report_id = r.id
        WHERE r.user_id = ?
        ORDER BY h.created_at DESC LIMIT 5
    """, (user_id,))
    activities = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "stats": {
            "total": counts['total'] or 0,
            "pending": counts['pending'] or 0,
            "in_progress": counts['in_progress'] or 0,
            "resolved": counts['resolved'] or 0
        },
        "status_distribution": status_dist,
        "recent_activities": activities
    }), 200

# ==========================================
# GENERAL REPORT DETAILS & TRACKING API
# ==========================================

@app.route('/api/reports/<complaint_id>', methods=['GET'])
def api_get_report_detail(complaint_id):
    """
    Returns complete report details, timeline progress history, and team info.
    Citizens can only view their own reports; admins can view all.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.*, u.full_name as reporter_name, u.email as reporter_email, u.phone as reporter_phone,
               t.team_name, t.lead_name, t.contact_number as team_contact, t.ward as team_ward
        FROM reports r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN cleanup_teams t ON r.assigned_team_id = t.id
        WHERE r.complaint_id = ?
    """, (complaint_id,))
    report_row = cursor.fetchone()

    if not report_row:
        conn.close()
        return jsonify({"error": f"Report '{complaint_id}' not found."}), 404

    report = dict(report_row)

    # Authorization check
    if 'user_id' not in session:
        conn.close()
        return jsonify({"error": "Please log in to track this complaint."}), 401

    if session.get('role') != 'admin' and report['user_id'] != session.get('user_id'):
        conn.close()
        return jsonify({"error": "You do not have permission to view this report."}), 403

    # Parse priority factors if present
    if report.get('priority_factors'):
        try:
            report['priority_factors'] = json.loads(report['priority_factors'])
        except Exception:
            report['priority_factors'] = []

    # Fetch audit history
    cursor.execute("""
        SELECT * FROM report_history
        WHERE report_id = ?
        ORDER BY created_at ASC
    """, (report['id'],))
    history = [dict(h) for h in cursor.fetchall()]
    conn.close()

    # Define standard 5-stage progress pipeline
    stages = [
        {"key": "Pending", "title": "Report Submitted", "desc": "Citizen reported waste with AI photo analysis."},
        {"key": "Reviewed", "title": "Report Reviewed", "desc": "Municipal admin reviewed priority & verified details."},
        {"key": "Assigned", "title": "Cleanup Assigned", "desc": "Dispatched to designated sanitation squad."},
        {"key": "In Progress", "title": "Cleanup In Progress", "desc": "Sanitation crew active on site."},
        {"key": "Resolved", "title": "Resolved", "desc": "Waste cleared and verified with photographic proof."}
    ]

    # Map current status to stage index
    stage_keys = ["Pending", "Reviewed", "Assigned", "In Progress", "Resolved"]
    current_status = report['status']
    current_index = stage_keys.index(current_status) if current_status in stage_keys else 0

    timeline = []
    for idx, s in enumerate(stages):
        is_completed = idx <= current_index
        is_current = idx == current_index
        
        # Match history event if exists
        matched_event = next((h for h in history if h['status'] == s['key']), None)
        timestamp = matched_event['created_at'] if matched_event else None
        note = matched_event['notes'] if matched_event else s['desc']
        actor = matched_event['changed_by'] if matched_event else None

        timeline.append({
            "stage": s['key'],
            "title": s['title'],
            "is_completed": is_completed,
            "is_current": is_current,
            "timestamp": timestamp,
            "note": note,
            "actor": actor
        })

    return jsonify({
        "report": report,
        "history": history,
        "timeline": timeline
    }), 200

# ==========================================
# ADMIN DASHBOARD & TRIAGE REST APIS
# ==========================================

@app.route('/api/admin/stats', methods=['GET'])
@login_required(role='admin')
def api_admin_stats():
    """Returns comprehensive analytics for the Admin Dashboard and Chart.js charts."""
    conn = get_db()
    cursor = conn.cursor()

    # KPI summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN priority_level IN ('High', 'Urgent') AND status != 'Resolved' THEN 1 ELSE 0 END) as high_priority,
            SUM(CASE WHEN status IN ('Reviewed', 'Assigned', 'In Progress') THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved
        FROM reports
    """)
    kpi = dict(cursor.fetchone())

    # Reports by Category
    cursor.execute("""
        SELECT waste_category, COUNT(*) as count 
        FROM reports 
        GROUP BY waste_category
        ORDER BY count DESC
    """)
    by_category = {row['waste_category']: row['count'] for row in cursor.fetchall()}

    # Reports by Status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM reports 
        GROUP BY status
    """)
    by_status = {row['status']: row['count'] for row in cursor.fetchall()}

    # Reports over Time (grouped by date)
    cursor.execute("""
        SELECT SUBSTR(created_at, 1, 10) as report_date, COUNT(*) as count
        FROM reports
        GROUP BY report_date
        ORDER BY report_date ASC
        LIMIT 14
    """)
    trend_rows = cursor.fetchall()
    trend = [{"date": r['report_date'], "count": r['count']} for r in trend_rows]

    # Recent Reports
    cursor.execute("""
        SELECT r.complaint_id, r.waste_category, r.address, r.priority_score, 
               r.priority_level, r.status, r.created_at, u.full_name as reporter_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
        LIMIT 8
    """)
    recent = [dict(r) for r in cursor.fetchall()]

    # Recent Audit Log
    cursor.execute("""
        SELECT h.*, r.complaint_id
        FROM report_history h
        JOIN reports r ON h.report_id = r.id
        ORDER BY h.created_at DESC
        LIMIT 6
    """)
    feed = [dict(f) for f in cursor.fetchall()]

    conn.close()

    return jsonify({
        "kpi": {
            "total": kpi['total'] or 0,
            "pending": kpi['pending'] or 0,
            "high_priority": kpi['high_priority'] or 0,
            "in_progress": kpi['in_progress'] or 0,
            "resolved": kpi['resolved'] or 0
        },
        "by_category": by_category,
        "by_status": by_status,
        "trend": trend,
        "recent_reports": recent,
        "activity_feed": feed
    }), 200

@app.route('/api/admin/reports', methods=['GET'])
@login_required(role='admin')
def api_admin_reports():
    """Returns filtered reports list for Report Management."""
    status = request.args.get('status', 'all').strip().lower()
    category = request.args.get('category', 'all').strip()
    priority = request.args.get('priority', 'all').strip()
    search = request.args.get('search', '').strip().lower()

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT r.*, u.full_name as reporter_name, t.team_name, t.lead_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN cleanup_teams t ON r.assigned_team_id = t.id
        WHERE 1=1
    """
    params = []

    if status and status != 'all':
        query += " AND LOWER(r.status) = ?"
        params.append(status)

    if category and category != 'all':
        query += " AND r.waste_category = ?"
        params.append(category)

    if priority and priority != 'all':
        query += " AND r.priority_level = ?"
        params.append(priority)

    if search:
        query += " AND (LOWER(r.complaint_id) LIKE ? OR LOWER(r.address) LIKE ? OR LOWER(r.description) LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    query += " ORDER BY r.priority_score DESC, r.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    reports = []
    for r in rows:
        item = dict(r)
        if item.get('priority_factors'):
            try:
                item['priority_factors'] = json.loads(item['priority_factors'])
            except Exception:
                item['priority_factors'] = []
        reports.append(item)

    return jsonify({"reports": reports, "count": len(reports)}), 200

@app.route('/api/admin/hotspots', methods=['GET'])
@login_required(role='admin')
def api_admin_hotspots():
    """
    Executes Scikit-learn DBSCAN clustering on report coordinates.
    Filters by category, status, priority.
    Returns cluster groups, noise points, and spatial metrics.
    """
    category = request.args.get('category', 'all').strip()
    status = request.args.get('status', 'all').strip().lower()
    priority = request.args.get('priority', 'all').strip()
    eps_meters = float(request.args.get('eps', 700.0))
    min_samples = int(request.args.get('min_samples', 2))

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT r.id, r.complaint_id, r.latitude, r.longitude, r.waste_category,
               r.priority_score, r.priority_level, r.status, r.address, r.image_url,
               r.created_at, u.full_name as reporter_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE 1=1
    """
    params = []

    if category and category != 'all':
        query += " AND r.waste_category = ?"
        params.append(category)

    if status and status != 'all':
        query += " AND LOWER(r.status) = ?"
        params.append(status)

    if priority and priority != 'all':
        query += " AND r.priority_level = ?"
        params.append(priority)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    reports = [dict(r) for r in rows]

    # Run DBSCAN Clustering
    clustering_results = run_dbscan_clustering(reports, eps_meters=eps_meters, min_samples=min_samples)

    # Compute summary KPIs for side panel
    total_in_view = len(reports)
    awaiting_cleanup = sum(1 for r in reports if r['status'] in ['Pending', 'Reviewed', 'Assigned'])
    high_priority_count = sum(1 for r in reports if r['priority_level'] in ['High', 'Urgent'])

    clustering_results['summary'] = {
        "total_reports": total_in_view,
        "detected_clusters": clustering_results['cluster_count'],
        "awaiting_cleanup": awaiting_cleanup,
        "high_priority_reports": high_priority_count
    }

    return jsonify(clustering_results), 200

@app.route('/api/admin/teams', methods=['GET'])
@login_required(role='admin')
def api_admin_teams():
    """Returns available cleanup teams with active workload."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, 
               (SELECT COUNT(*) FROM reports WHERE assigned_team_id = t.id AND status IN ('Assigned', 'In Progress')) as current_load
        FROM cleanup_teams t
        ORDER BY t.ward ASC
    """)
    teams = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"teams": teams}), 200

@app.route('/api/admin/reports/<complaint_id>/update', methods=['POST'])
@login_required(role='admin')
def api_admin_update_report(complaint_id):
    """
    Admin updates report: status, team assignment, admin notes, proof photo upload.
    Updates SQLite and records an audit history entry.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports WHERE complaint_id = ?", (complaint_id,))
    report = cursor.fetchone()
    if not report:
        conn.close()
        return jsonify({"error": f"Report '{complaint_id}' not found."}), 404

    # Extract update fields
    new_status = request.form.get('status', report['status']).strip()
    team_id_raw = request.form.get('assigned_team_id')
    new_team_id = int(team_id_raw) if team_id_raw and team_id_raw.isdigit() else report['assigned_team_id']
    admin_notes = request.form.get('admin_notes', report['admin_notes'] or '').strip()
    
    # Check for after-cleanup proof image upload
    after_image_url = report['after_image_url']
    if 'after_image' in request.files:
        after_file = request.files['after_image']
        if after_file.filename != '' and allowed_file(after_file.filename):
            ext = after_file.filename.rsplit('.', 1)[1].lower()
            proof_filename = f"proof_{uuid.uuid4().hex[:12]}.{ext}"
            proof_path = os.path.join(Config.UPLOAD_FOLDER, proof_filename)
            after_file.save(proof_path)
            after_image_url = f"/static/uploads/{proof_filename}"

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Update reports table
    cursor.execute("""
        UPDATE reports
        SET status = ?, assigned_team_id = ?, admin_notes = ?,
            after_image_url = ?, updated_at = ?
        WHERE complaint_id = ?
    """, (new_status, new_team_id, admin_notes, after_image_url, now_str, complaint_id))

    # Add history log if status changed or notes added
    admin_name = session.get('user_name', 'Administrator')
    history_note = f"Status updated to '{new_status}'."
    if new_team_id != report['assigned_team_id']:
        cursor.execute("SELECT team_name FROM cleanup_teams WHERE id = ?", (new_team_id,))
        team_row = cursor.fetchone()
        team_name = team_row['team_name'] if team_row else 'Assigned Team'
        history_note += f" Dispatched to {team_name}."
    if admin_notes:
        history_note += f" Note: {admin_notes}"
    if after_image_url != report['after_image_url']:
        history_note += " After-cleanup proof photo attached."

    cursor.execute("""
        INSERT INTO report_history (report_id, status, changed_by, notes, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (report['id'], new_status, admin_name, history_note, now_str))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Complaint {complaint_id} updated successfully.",
        "status": new_status,
        "after_image_url": after_image_url
    }), 200

def ensure_db_ready():
    try:
        init_db()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            from seed_data import seed_database
            conn.close()
            seed_database()
        else:
            conn.close()
    except Exception as e:
        print(f"Database readiness check notice: {e}")

ensure_db_ready()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

