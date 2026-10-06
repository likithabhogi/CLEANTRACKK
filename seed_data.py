import os
import json
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from config import Config
from database import init_db, get_db
from services.priority_service import calculate_priority_score

def create_sample_svg_images():
    """Generates clean placeholder SVG images for demo reports."""
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    samples = {
        "waste_plastic_bottles.svg": (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">'
            '<rect width="100%" height="100%" fill="#f1f5f9"/>'
            '<rect x="20" y="20" width="360" height="260" rx="12" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="2"/>'
            '<circle cx="200" cy="130" r="60" fill="#38bdf8" opacity="0.3"/>'
            '<path d="M190 70 L210 70 L210 90 L220 110 L220 190 L180 190 L180 110 L190 90 Z" fill="#0284c7"/>'
            '<rect x="185" y="60" width="30" height="10" rx="3" fill="#0369a1"/>'
            '<path d="M150 140 L170 140 L175 200 L145 200 Z" fill="#38bdf8" opacity="0.8"/>'
            '<path d="M225 150 L245 150 L250 205 L220 205 Z" fill="#0ea5e9" opacity="0.8"/>'
            '<text x="200" y="240" font-family="sans-serif" font-size="16" font-weight="bold" fill="#0369a1" text-anchor="middle">Discarded Plastic Bottles</text>'
            '<text x="200" y="260" font-family="sans-serif" font-size="12" fill="#64748b" text-anchor="middle">CleanTrack AI Visual Proof (Sample)</text>'
            '</svg>'
        ),
        "waste_organic_pile.svg": (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">'
            '<rect width="100%" height="100%" fill="#fefce8"/>'
            '<rect x="20" y="20" width="360" height="260" rx="12" fill="#fef08a" stroke="#facc15" stroke-width="2"/>'
            '<circle cx="200" cy="130" r="60" fill="#84cc16" opacity="0.3"/>'
            '<path d="M130 190 Q200 100 270 190 Z" fill="#65a30d"/>'
            '<circle cx="170" cy="170" r="18" fill="#4d7c0f"/>'
            '<circle cx="220" cy="165" r="22" fill="#3f6212"/>'
            '<path d="M185 140 Q200 120 215 140 Q200 160 185 140 Z" fill="#a3e635"/>'
            '<text x="200" y="240" font-family="sans-serif" font-size="16" font-weight="bold" fill="#3f6212" text-anchor="middle">Organic &amp; Food Waste Pile</text>'
            '<text x="200" y="260" font-family="sans-serif" font-size="12" fill="#713f12" text-anchor="middle">CleanTrack AI Visual Proof (Sample)</text>'
            '</svg>'
        ),
        "waste_mixed_dump.svg": (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">'
            '<rect width="100%" height="100%" fill="#fff1f2"/>'
            '<rect x="20" y="20" width="360" height="260" rx="12" fill="#ffe4e6" stroke="#fda4af" stroke-width="2"/>'
            '<path d="M110 200 L160 120 L240 130 L290 200 Z" fill="#e11d48" opacity="0.8"/>'
            '<rect x="140" y="160" width="40" height="40" rx="4" fill="#64748b"/>'
            '<circle cx="220" cy="170" r="20" fill="#fb923c"/>'
            '<path d="M190 140 L210 140 L205 180 L185 180 Z" fill="#38bdf8"/>'
            '<text x="200" y="240" font-family="sans-serif" font-size="16" font-weight="bold" fill="#9f1239" text-anchor="middle">Mixed Urban Overflow Dump</text>'
            '<text x="200" y="260" font-family="sans-serif" font-size="12" fill="#881337" text-anchor="middle">CleanTrack AI Visual Proof (Sample)</text>'
            '</svg>'
        ),
        "waste_metal_cans.svg": (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">'
            '<rect width="100%" height="100%" fill="#f8fafc"/>'
            '<rect x="20" y="20" width="360" height="260" rx="12" fill="#e2e8f0" stroke="#94a3b8" stroke-width="2"/>'
            '<rect x="140" y="120" width="40" height="70" rx="6" fill="#64748b"/>'
            '<rect x="200" y="110" width="45" height="80" rx="6" fill="#94a3b8"/>'
            '<ellipse cx="160" cy="120" rx="20" ry="8" fill="#475569"/>'
            '<ellipse cx="222" cy="110" rx="22" ry="8" fill="#64748b"/>'
            '<text x="200" y="240" font-family="sans-serif" font-size="16" font-weight="bold" fill="#334155" text-anchor="middle">Metal Cans &amp; Scrap Debris</text>'
            '<text x="200" y="260" font-family="sans-serif" font-size="12" fill="#64748b" text-anchor="middle">CleanTrack AI Visual Proof (Sample)</text>'
            '</svg>'
        ),
        "proof_cleaned_spot.svg": (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">'
            '<rect width="100%" height="100%" fill="#f0fdf4"/>'
            '<rect x="20" y="20" width="360" height="260" rx="12" fill="#dcfce7" stroke="#86efac" stroke-width="2"/>'
            '<circle cx="200" cy="120" r="50" fill="#22c55e" opacity="0.2"/>'
            '<path d="M170 120 L190 140 L235 95" stroke="#16a34a" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
            '<path d="M120 180 Q200 170 280 180" stroke="#86efac" stroke-width="4" fill="none"/>'
            '<text x="200" y="225" font-family="sans-serif" font-size="17" font-weight="bold" fill="#15803d" text-anchor="middle">VERIFIED CLEANED AREA</text>'
            '<text x="200" y="250" font-family="sans-serif" font-size="12" fill="#166534" text-anchor="middle">Municipal Sanitation Squad Resolution Proof</text>'
            '</svg>'
        )
    }

    for filename, content in samples.items():
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

def seed_database():
    init_db()
    create_sample_svg_images()
    
    conn = get_db()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        print("Database already contains data. Skipping re-seed.")
        conn.close()
        return

    print("Seeding CleanTrack AI database with users, teams, and sample reports...")

    # 1. Seed Users (Demo Citizen & Demo Admin)
    citizen_pw = generate_password_hash("Citizen123!")
    admin_pw = generate_password_hash("Admin123!")

    users = [
        ("Priya Sharma", "citizen@cleantrack.ai", "+91 98765 43210", citizen_pw, "citizen"),
        ("Rahul Verma", "rahul@cleantrack.ai", "+91 98111 22334", citizen_pw, "citizen"),
        ("Chief Admin Officer Rajesh", "admin@cleantrack.ai", "+91 99887 76655", admin_pw, "admin")
    ]
    cursor.executemany("""
        INSERT INTO users (full_name, email, phone, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
    """, users)

    citizen1_id = 1
    citizen2_id = 2

    # 2. Seed Cleanup Teams
    teams = [
        ("Ward 4 Rapid Response Unit", "Ward 4 - Indiranagar", "Vikram Singh", "+91 98221 00111", "Available", 1),
        ("EcoClean Green Crew", "Ward 2 - Koramangala", "Anita Patel", "+91 98221 00222", "Dispatched", 2),
        ("Central Municipal Sanitation Crew #3", "Ward 7 - MG Road Zone", "David D'Souza", "+91 98221 00333", "Available", 0),
        ("North Zone Waste Logistics Squad", "Ward 9 - Malleshwaram", "Sunita Rao", "+91 98221 00444", "Busy", 1)
    ]
    cursor.executemany("""
        INSERT INTO cleanup_teams (team_name, ward, lead_name, contact_number, status, active_assignments)
        VALUES (?, ?, ?, ?, ?, ?)
    """, teams)

    # 3. Seed Realistic Reports with Cluster Coordinates
    # Center: Bengaluru urban zone approx lat: 12.9716, lng: 77.5946
    # Cluster 1: Indiranagar 100ft Road cluster (3 reports close together)
    # Cluster 2: Koramangala 4th Block cluster (4 reports close together)
    # Cluster 3: MG Road Commercial cluster (2 reports close together)
    # Noise points: Isolated reports (2 reports far away)

    now = datetime.now()

    sample_reports = [
        # Cluster 1: Indiranagar Market Area (Cluster 0)
        {
            "complaint_id": "CT-2026-1042",
            "user_id": citizen1_id,
            "image": "waste_plastic_bottles.svg",
            "after_image": None,
            "category": "Plastic",
            "ai_pred": "Plastic",
            "ai_conf": 94.6,
            "desc": "Piles of plastic packaging and mineral water bottles dumped behind supermarket near school drain.",
            "lat": 12.9784,
            "lng": 77.6408,
            "address": "12th Main Road, Near National Public School, Indiranagar",
            "status": "Pending",
            "team_id": None,
            "admin_notes": "Pending inspection dispatch.",
            "hours_ago": 6,
            "in_cluster": True
        },
        {
            "complaint_id": "CT-2026-1043",
            "user_id": citizen1_id,
            "image": "waste_organic_pile.svg",
            "after_image": None,
            "category": "Organic",
            "ai_pred": "Organic",
            "ai_conf": 96.1,
            "desc": "Decomposing market vegetable waste overflowing near fruit stall. Severe foul smell attracting stray animals.",
            "lat": 12.9792,
            "lng": 77.6415,
            "address": "100ft Road Junction, Indiranagar Market Gate #2",
            "status": "In Progress",
            "team_id": 1,
            "admin_notes": "Dispatched Ward 4 Rapid Response Unit. Clearing underway.",
            "hours_ago": 26,
            "in_cluster": True
        },
        {
            "complaint_id": "CT-2026-1044",
            "user_id": citizen2_id,
            "image": "waste_mixed_dump.svg",
            "after_image": "proof_cleaned_spot.svg",
            "category": "Mixed Waste",
            "ai_pred": "Mixed Waste",
            "ai_conf": 91.8,
            "desc": "Mixed street garbage blocking pedestrian sidewalk near Indiranagar metro pillar 42.",
            "lat": 12.9778,
            "lng": 77.6420,
            "address": "Metro Pillar 42, CMH Road, Indiranagar",
            "status": "Resolved",
            "team_id": 1,
            "admin_notes": "Cleared completely by Team Vikram Singh. Area sanitized with lime powder.",
            "hours_ago": 48,
            "in_cluster": True
        },

        # Cluster 2: Koramangala Zone (Cluster 1)
        {
            "complaint_id": "CT-2026-1050",
            "user_id": citizen1_id,
            "image": "waste_mixed_dump.svg",
            "after_image": None,
            "category": "Mixed Waste",
            "ai_pred": "Mixed Waste",
            "ai_conf": 93.4,
            "desc": "Severe garbage pile next to stormwater drain near Apollo clinic. Hospital waste mixed with plastic.",
            "lat": 12.9345,
            "lng": 77.6265,
            "address": "80 Feet Rd, 4th Block, Near Clinic, Koramangala",
            "status": "Assigned",
            "team_id": 2,
            "admin_notes": "High priority assigned due to medical facility proximity.",
            "hours_ago": 18,
            "in_cluster": True
        },
        {
            "complaint_id": "CT-2026-1051",
            "user_id": citizen2_id,
            "image": "waste_plastic_bottles.svg",
            "after_image": None,
            "category": "Plastic",
            "ai_pred": "Plastic",
            "ai_conf": 95.0,
            "desc": "Dozens of plastic takeaway food containers thrown along park boundary wall.",
            "lat": 12.9352,
            "lng": 77.6258,
            "address": "Koramangala 4th Block Playground perimeter",
            "status": "Reviewed",
            "team_id": None,
            "admin_notes": "Reviewed by Admin. Awaiting team allocation.",
            "hours_ago": 14,
            "in_cluster": True
        },
        {
            "complaint_id": "CT-2026-1052",
            "user_id": citizen1_id,
            "image": "waste_metal_cans.svg",
            "after_image": None,
            "category": "Metal/Glass",
            "ai_pred": "Metal/Glass",
            "ai_conf": 89.2,
            "desc": "Discarded broken bottles and metal construction scrap on cycle track corner.",
            "lat": 12.9360,
            "lng": 77.6270,
            "address": "Sony World Signal Service Road, Koramangala",
            "status": "In Progress",
            "team_id": 2,
            "admin_notes": "EcoClean Green Crew deployed. Work started.",
            "hours_ago": 30,
            "in_cluster": True
        },
        {
            "complaint_id": "CT-2026-1053",
            "user_id": citizen2_id,
            "image": "waste_organic_pile.svg",
            "after_image": "proof_cleaned_spot.svg",
            "category": "Organic",
            "ai_pred": "Organic",
            "ai_conf": 92.5,
            "desc": "Tree trimmings and rotten leaves clogging drainage culvert.",
            "lat": 12.9338,
            "lng": 77.6260,
            "address": "5th Cross, 4th Block, Koramangala",
            "status": "Resolved",
            "team_id": 2,
            "admin_notes": "Sanitation crew cleared drain inlet. Photo verified.",
            "hours_ago": 72,
            "in_cluster": True
        },

        # Cluster 3: MG Road / Brigade Rd (Cluster 2)
        {
            "complaint_id": "CT-2026-1060",
            "user_id": citizen1_id,
            "image": "waste_plastic_bottles.svg",
            "after_image": None,
            "category": "Plastic",
            "ai_pred": "Plastic",
            "ai_conf": 92.0,
            "desc": "Commercial plastic trash and shopping bags overflowing municipal dustbins.",
            "lat": 12.9750,
            "lng": 77.6070,
            "address": "Brigade Road Commercial Walkway, MG Road",
            "status": "Pending",
            "team_id": None,
            "admin_notes": "Queued for morning municipal round.",
            "hours_ago": 4,
            "in_cluster": True
        },
        {
            "complaint_id": "CT-2026-1061",
            "user_id": citizen2_id,
            "image": "waste_mixed_dump.svg",
            "after_image": None,
            "category": "Mixed Waste",
            "ai_pred": "Mixed Waste",
            "ai_conf": 93.1,
            "desc": "Debris pile left behind after night street food stalls.",
            "lat": 12.9756,
            "lng": 77.6081,
            "address": "Church Street intersection, MG Road",
            "status": "Reviewed",
            "team_id": None,
            "admin_notes": "Inspected, high pedestrian footfall.",
            "hours_ago": 10,
            "in_cluster": True
        },

        # Isolated Noise Points (label -1 in DBSCAN)
        {
            "complaint_id": "CT-2026-1070",
            "user_id": citizen1_id,
            "image": "waste_metal_cans.svg",
            "after_image": None,
            "category": "Metal/Glass",
            "ai_pred": "Metal/Glass",
            "ai_conf": 88.5,
            "desc": "Isolated bag of rusted metal cans and nails dumped on vacant lot.",
            "lat": 13.0035,
            "lng": 77.5680,
            "address": "15th Cross Road, Malleshwaram West",
            "status": "Pending",
            "team_id": None,
            "admin_notes": "Isolated incident. Logged.",
            "hours_ago": 8,
            "in_cluster": False
        },
        {
            "complaint_id": "CT-2026-1071",
            "user_id": citizen2_id,
            "image": "waste_organic_pile.svg",
            "after_image": "proof_cleaned_spot.svg",
            "category": "Organic",
            "ai_pred": "Organic",
            "ai_conf": 94.0,
            "desc": "Discarded coconut shells and garden trimmings outside residential gate.",
            "lat": 12.9150,
            "lng": 77.5850,
            "address": "9th Main, Jayanagar 3rd Block",
            "status": "Resolved",
            "team_id": 3,
            "admin_notes": "Cleared by Central sanitation team. Photo evidence confirmed.",
            "hours_ago": 52,
            "in_cluster": False
        }
    ]

    for item in sample_reports:
        created_time = (now - timedelta(hours=item['hours_ago'])).strftime('%Y-%m-%d %H:%M:%S')
        updated_time = (now - timedelta(hours=max(0, item['hours_ago'] - 2))).strftime('%Y-%m-%d %H:%M:%S')

        # Calculate Priority
        p_calc = calculate_priority_score(
            waste_category=item['category'],
            description=item['desc'],
            address=item['address'],
            hours_elapsed=item['hours_ago'],
            is_in_cluster=item['in_cluster']
        )

        cursor.execute("""
            INSERT INTO reports (
                complaint_id, user_id, image_url, after_image_url,
                waste_category, ai_predicted_category, ai_confidence,
                description, latitude, longitude, address,
                priority_score, priority_level, priority_factors,
                status, assigned_team_id, admin_notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item['complaint_id'],
            item['user_id'],
            f"/static/uploads/{item['image']}",
            f"/static/uploads/{item['after_image']}" if item['after_image'] else None,
            item['category'],
            item['ai_pred'],
            item['ai_conf'],
            item['desc'],
            item['lat'],
            item['lng'],
            item['address'],
            p_calc['score'],
            p_calc['level'],
            json.dumps(p_calc['factors']),
            item['status'],
            item['team_id'],
            item['admin_notes'],
            created_time,
            updated_time
        ))

        report_id = cursor.lastrowid

        # Insert audit history entries
        cursor.execute("""
            INSERT INTO report_history (report_id, status, changed_by, notes, created_at)
            VALUES (?, 'Pending', 'Citizen via Mobile Web', 'Complaint registered with AI photo verification', ?)
        """, (report_id, created_time))

        if item['status'] in ['Reviewed', 'Assigned', 'In Progress', 'Resolved']:
            cursor.execute("""
                INSERT INTO report_history (report_id, status, changed_by, notes, created_at)
                VALUES (?, 'Reviewed', 'Admin Officer Rajesh', 'Priority assessed and complaint verified', ?)
            """, (report_id, (now - timedelta(hours=item['hours_ago'] - 1)).strftime('%Y-%m-%d %H:%M:%S')))

        if item['status'] in ['Assigned', 'In Progress', 'Resolved']:
            cursor.execute("""
                INSERT INTO report_history (report_id, status, changed_by, notes, created_at)
                VALUES (?, 'Assigned', 'Admin Officer Rajesh', 'Assigned to cleanup team', ?)
            """, (report_id, (now - timedelta(hours=item['hours_ago'] - 2)).strftime('%Y-%m-%d %H:%M:%S')))

        if item['status'] in ['In Progress', 'Resolved']:
            cursor.execute("""
                INSERT INTO report_history (report_id, status, changed_by, notes, created_at)
                VALUES (?, 'In Progress', 'Cleanup Squad Lead', 'Team arrived at site. Clearance underway.', ?)
            """, (report_id, (now - timedelta(hours=item['hours_ago'] - 3)).strftime('%Y-%m-%d %H:%M:%S')))

        if item['status'] == 'Resolved':
            cursor.execute("""
                INSERT INTO report_history (report_id, status, changed_by, notes, created_at)
                VALUES (?, 'Resolved', 'Admin Officer Rajesh', 'Resolution verified with after-cleanup photo evidence', ?)
            """, (report_id, updated_time))

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
