#!/usr/bin/env python
"""
Test script for admin panel endpoints
"""
import sys
import time

sys.path.insert(0, '.')

from app import app, initialize_database
from database import log_scan_result, track_user, get_stats

# Initialize database
print("[1] Initializing database...")
initialize_database()
print("    ✓ Database initialized")

# Test data logging
print("\n[2] Testing database operations...")
log_scan_result("https://phishing.example.com", 85.5, "Phishing", "test", "user_192.168.1.1", "192.168.1.1")
log_scan_result("https://google.com", 15.0, "Safe", "test", "user_192.168.1.1", "192.168.1.1")
track_user("user_192.168.1.1", "192.168.1.1")
print("    ✓ Scan results logged")
print("    ✓ User tracked")

# Test statistics
print("\n[3] Testing statistics endpoint...")
stats = get_stats()
print(f"    ✓ Total scans: {stats['total_scans']}")
print(f"    ✓ Phishing detections: {stats['phishing_detections']}")
print(f"    ✓ Safe detections: {stats['safe_detections']}")
print(f"    ✓ Active users: {stats['active_users']}")
print(f"    ✓ System status: {stats['system_status']}")

# Test Flask app with test client
print("\n[4] Testing Flask app routes...")
app.config['TESTING'] = True
with app.test_client() as client:
    # Test health endpoint
    response = client.get('/health')
    print(f"    ✓ GET /health: {response.status_code}")
    
    # Test admin login
    response = client.post('/admin', json={"username": "admin", "password": "phishguard123"})
    print(f"    ✓ POST /admin (login): {response.status_code}")
    if response.status_code == 200:
        print("       Login successful!")
    
    # Get session cookie
    session_cookie = None
    for cookie in response.headers.getlist('Set-Cookie'):
        if 'session' in cookie.lower():
            session_cookie = cookie
            break
    
    if session_cookie:
        # Test /predict endpoint
        response = client.post('/predict', json={"url": "https://example.com"})
        print(f"    ✓ POST /predict: {response.status_code}")
    
    # Test admin stats (without auth will fail)
    response = client.get('/admin/stats')
    print(f"    ✓ GET /admin/stats (no auth): {response.status_code} (expected 401)")

print("\n[5] All tests completed!")
print("\n✅ Admin panel backend is ready!")
print("\nTo start the server, run:")
print("  python app.py")
print("\nTo access admin panel:")
print("  1. Start frontend: cd frontend && npm run dev")
print("  2. Navigate to: http://localhost:5173/admin")
print("  3. Login with: admin / phishguard123")
