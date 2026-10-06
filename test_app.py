import io
from app import app
from database import get_db

def run_tests():
    print("=== Running CleanTrack AI System Integration Tests ===")
    client = app.test_client()

    # 1. Test Page 1: Home Page
    res = client.get('/')
    assert res.status_code == 200, f"Page 1 failed: {res.status_code}"
    assert b"Making Our Cities Cleaner with" in res.data, "Page 1 heading missing"
    assert b"Report Garbage" in res.data, "Page 1 CTA missing"
    print("PASS: Page 1 (Home Page) renders successfully.")

    # 2. Test Page 2: Login and Registration Page
    res = client.get('/login')
    assert res.status_code == 200, f"Page 2 failed: {res.status_code}"
    assert b"Welcome Back to CleanTrack AI" in res.data, "Page 2 login header missing"
    assert b"Citizen Demo" in res.data, "Page 2 demo buttons missing"
    print("PASS: Page 2 (Login/Register) renders successfully.")

    # Test Login API with Citizen credentials
    res = client.post('/api/auth/login', json={
        "email": "citizen@cleantrack.ai",
        "password": "Citizen123!",
        "remember": True
    })
    assert res.status_code == 200, f"Login failed: {res.json}"
    assert res.json['success'] is True
    print("PASS: Citizen authentication successful.")

    # 3. Test Page 3: Citizen Dashboard
    res = client.get('/citizen/dashboard')
    assert res.status_code == 200, f"Page 3 failed: {res.status_code}"
    assert b"Citizen Services" in res.data
    assert b"citizenStatusChart" in res.data
    print("PASS: Page 3 (Citizen Dashboard) renders successfully.")

    # Test Citizen Stats API
    res = client.get('/api/citizen/stats')
    assert res.status_code == 200, f"Citizen stats API failed: {res.status_code}"
    stats = res.json['stats']
    print(f"Citizen Stats: Total={stats['total']}, Pending={stats['pending']}, InProgress={stats['in_progress']}, Resolved={stats['resolved']}")

    # 4. Test Page 4: Report Garbage Page
    res = client.get('/report')
    assert res.status_code == 200, f"Page 4 failed: {res.status_code}"
    assert b"Report Street Garbage" in res.data
    assert b"reportMap" in res.data
    print("PASS: Page 4 (Report Garbage) renders successfully.")

    # Test AI Waste Classification API with mock dummy image
    dummy_img = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82")
    res = client.post('/api/ai/classify-waste', data={'image': (dummy_img, 'test.png')}, content_type='multipart/form-data')
    assert res.status_code == 200, f"AI classification failed: {res.json}"
    ai_data = res.json
    print(f"PASS: AI classification API returned: {ai_data['predicted_category']} ({ai_data['confidence']}%)")

    # Test Report Submission API
    dummy_img2 = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82")
    res = client.post('/api/reports', data={
        'image': (dummy_img2, 'new_report.png'),
        'latitude': '12.9780',
        'longitude': '77.6410',
        'waste_category': 'Plastic',
        'description': 'Plastic bottles clogging school drain and pathway',
        'address': '12th Main Road, Indiranagar',
        'ai_predicted_category': 'Plastic',
        'ai_confidence': '95.5'
    }, content_type='multipart/form-data')
    assert res.status_code == 201, f"Report submission failed: {res.json}"
    new_complaint_id = res.json['complaint_id']
    print(f"PASS: Report submission created complaint ID: {new_complaint_id}")

    # 5. Test Page 5: My Reports and Tracking
    res = client.get('/my-reports')
    assert res.status_code == 200, f"Page 5 failed: {res.status_code}"
    assert b"My Reports &amp; Tracking" in res.data
    assert b"modalTimelineContainer" in res.data
    print("PASS: Page 5 (My Reports and Tracking) renders successfully.")

    # Test Tracking Details API
    res = client.get(f'/api/reports/{new_complaint_id}')
    assert res.status_code == 200, f"Tracking detail failed: {res.json}"
    timeline = res.json['timeline']
    assert len(timeline) == 5, "5-stage timeline should have 5 stages"
    print(f"PASS: 5-Stage progress timeline verified: {[s['title'] for s in timeline]}")

    # Logout citizen
    client.post('/api/auth/logout')

    # Test Admin login
    res = client.post('/api/auth/login', json={
        "email": "admin@cleantrack.ai",
        "password": "Admin123!"
    })
    assert res.status_code == 200, f"Admin login failed: {res.json}"
    print("PASS: Administrator authentication successful.")

    # 6. Test Page 6: Admin Dashboard
    res = client.get('/admin/dashboard')
    assert res.status_code == 200, f"Page 6 failed: {res.status_code}"
    assert b"Administrator Dashboard" in res.data
    assert b"trendLineChart" in res.data
    assert b"categoryDoughnutChart" in res.data
    assert b"statusBarChart" in res.data
    print("PASS: Page 6 (Admin Dashboard) with 3 Chart.js graphs renders successfully.")

    # Test Admin Stats API
    res = client.get('/api/admin/stats')
    assert res.status_code == 200, f"Admin stats API failed: {res.status_code}"
    print(f"Admin Stats: Total={res.json['kpi']['total']}, HighPriority={res.json['kpi']['high_priority']}")

    # 7. Test Page 7: Garbage Hotspot Map
    res = client.get('/admin/hotspots')
    assert res.status_code == 200, f"Page 7 failed: {res.status_code}"
    assert b"Garbage Hotspot Monitoring" in res.data
    assert b"hotspotMapCanvas" in res.data
    print("PASS: Page 7 (Garbage Hotspot Map) renders successfully.")

    # Test DBSCAN Hotspots API
    res = client.get('/api/admin/hotspots?eps=700')
    assert res.status_code == 200, f"Hotspots API failed: {res.status_code}"
    hotspots = res.json
    print(f"PASS: DBSCAN Clustering identified {hotspots['cluster_count']} dense clusters and {len(hotspots['noise_points'])} noise points.")

    # 8. Test Page 8: Report Management and Cleanup
    res = client.get('/admin/reports')
    assert res.status_code == 200, f"Page 8 failed: {res.status_code}"
    assert b"Report Management &amp; Cleanup Dispatch" in res.data
    assert b"triageFactorsList" in res.data
    print("PASS: Page 8 (Report Management and Cleanup) renders successfully.")

    # Test Admin Triage Update (assign team, change status, add notes)
    res = client.post(f'/api/admin/reports/{new_complaint_id}/update', data={
        'status': 'In Progress',
        'assigned_team_id': '1',
        'admin_notes': 'Dispatched Ward 4 Rapid response unit to clear the drain.'
    })
    assert res.status_code == 200, f"Triage update failed: {res.json}"
    print(f"PASS: Report {new_complaint_id} triaged and updated to In Progress.")

    print("\nALL 8 PAGES AND REST APIS PASSED INTEGRATION TESTS SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
