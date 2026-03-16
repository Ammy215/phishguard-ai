# PhishGuard AI - Admin Panel Setup & Deployment Guide

## 📋 Quick Start

### 1. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Start Backend
```bash
cd backend
python app.py
```
Backend runs on: **http://localhost:5000**

### 3. Start Frontend
```bash
cd frontend
npm run dev
```
Frontend runs on: **http://localhost:5173**

### 4. Access Admin Panel
Navigate to: **http://localhost:5173/admin**

Login with:
- Username: `admin`
- Password: `phishguard123`

---

## 🏗️ Architecture Overview

### Backend Components

#### Database Module (`database.py`)
- SQLite database for persistent storage
- 3 tables: `scan_results`, `users`, `banned_users`
- Thread-safe operations with locks
- Context manager for connections

#### Admin Endpoints (Flask)
```
Authentication:
  POST /admin (login)
  POST /admin/logout

Statistics:
  GET /admin/stats
  GET /admin/detection-stats

Scans:
  GET /admin/recent-scans

Users:
  GET /admin/users
  GET /admin/banned-users
  POST /admin/ban-user
  POST /admin/unban-user
```

#### Integration with /predict
- User tracking on every request
- Ban checking on every request
- Automatic scan logging to database
- Returns 403 "User is banned" for banned users

### Frontend Components

#### Pages
- **login.tsx**: Authentication interface
- **dashboard.tsx**: Main monitoring dashboard

#### Components
- **stats-cards.tsx**: 5-metric statistics display
- **detection-chart.tsx**: 7-day trend visualization
- **recent-scans-table.tsx**: Live scan history
- **users-table.tsx**: User management & banning
- **banned-users.tsx**: Banned users list
- **threat-status.tsx**: Threat feed status

---

## 📊 Database Schema

### scan_results
```sql
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    risk_score REAL NOT NULL,
    result TEXT NOT NULL,  -- SAFE or PHISHING
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL,  -- extension or dashboard
    user_id TEXT,
    ip_address TEXT
);
```

### users
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    ip_address TEXT NOT NULL,
    request_count INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',  -- active or banned
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### banned_users
```sql
CREATE TABLE banned_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    ban_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);
```

---

## 🔐 Security Features

### 1. Authentication
- Admin-only access with session cookies
- Hardcoded credentials (can be improved with JWT or OAuth)
- Session validation on all protected endpoints

### 2. User Banning
- Ban at API level (403 response)
- Prevents resource usage by malicious users
- Ban history maintained for audit

### 3. Activity Logging
- Every scan logged with timestamp, user, IP
- User tracking for analytics
- Enables incident investigation

### 4. CORS Protection
- Credentials required for cross-origin requests
- Session-based auth (no exposed tokens)

---

## 📈 Features Breakdown

### Statistics Dashboard
```
Total Scans: 1,234
├─ Phishing Detections: 456 (37%)
└─ Safe URLs: 778 (63%)

Active Users: 42
System Status: OPERATIONAL
```

### Detection Trends
- 7-day rolling chart
- Phishing vs Safe breakdown
- Hourly/daily aggregation
- Interactive tooltips

### Recent Scans Table
- Last 50 scans displayed
- Sortable columns (URL, Risk Score, Result, Time)
- Risk score color-coded
- Source indicator (extension/dashboard)

### User Management
- View all users with metrics
- Request count per user
- Ban/Unban functionality
- IP address tracking
- First seen / Last seen timestamps

### Threat Intelligence Status
- Shows all threat feeds
- Status indicators (ACTIVE/ERROR)
- Feed descriptions
- Last update timestamp

---

## 🚀 Deployment Considerations

### Production Backend
```python
# settings to change in app.py
debug = False  # Disable debug mode
ADMIN_PASSWORD = "use-strong-password"  # Change admin password
SECRET_KEY = "use-secure-random-key"  # Generate secure key
```

### Production Database
- Use PostgreSQL instead of SQLite for scale
- Set up automated backups
- Configure connection pooling
- Implement data archival policy

### Production Frontend
```bash
# Build for production
npm run build

# Serve with web server
# nginx, Apache, or Vercel recommended
```

### Environment Variables
Create `.env` in backend:
```
PORT=5000
FLASK_DEBUG=false
SECRET_KEY=your-generated-secret-key
CORS_ORIGINS=your-frontend-domain
ADMIN_PASSWORD=your-strong-password
```

---

## 🔧 Troubleshooting

### Admin Login Not Working
1. **Check backend running**: `curl http://localhost:5000/health`
2. **Check credentials**: Username must be `admin`
3. **Check CORS**: Browser console for CORS errors
4. **Clear cookies**: Browser may have old session data

### No Data Appearing
1. **Check /predict calls**: Extension should log scans
2. **Check database**: Verify phishguard.db exists
3. **Check backend logs**: Look for database errors
4. **Manual test**: Send POST to /predict endpoint

### User Not Banning
1. **Check user_id format**: Should match format in database
2. **Check banned_users table**: Verify ban entry created
3. **Check /predict logic**: Ensure is_user_banned check active
4. **Restart backend**: Clear any cached auth state

### Charts Not Loading
1. **Check detection-stats endpoint**: `curl http://localhost:5000/admin/detection-stats`
2. **Check data format**: Ensure stats have date field
3. **Check Recharts**: Verify library properly imported
4. **Check browser console**: Look for JavaScript errors

---

## 📦 Dependencies

### Backend
```
Flask==3.1.0
flask-cors==5.0.0
joblib
pandas
scikit-learn
requests
python-dotenv
```

### Frontend
```json
{
  "dependencies": {
    "@radix-ui/react-alert-dialog": "^1.0.5",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router-dom": "^7.12.0",
    "recharts": "^2.15.5",
    "lucide-react": "^0.562.0"
  }
}
```

---

## 📝 API Documentation

### POST /admin
**Login endpoint**
```bash
curl -X POST http://localhost:5000/admin \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"phishguard123"}'

# Response
{
  "success": true,
  "message": "Login successful"
}
```

### GET /admin/stats
**Get system statistics**
```bash
curl -X GET http://localhost:5000/admin/stats \
  -H "Cookie: session=..."

# Response
{
  "total_scans": 1234,
  "phishing_detections": 456,
  "safe_detections": 778,
  "active_users": 42,
  "system_status": "OPERATIONAL"
}
```

### GET /admin/recent-scans
**Get recent scan results**
```bash
curl -X GET "http://localhost:5000/admin/recent-scans?limit=20" \
  -H "Cookie: session=..."

# Response
{
  "scans": [
    {
      "id": 123,
      "url": "https://example.com",
      "risk_score": 65.5,
      "result": "PHISHING",
      "scan_time": "2024-03-16T10:30:00",
      "source": "extension"
    }
  ],
  "count": 1
}
```

### GET /admin/users
**Get all users**
```bash
curl -X GET "http://localhost:5000/admin/users?limit=100" \
  -H "Cookie: session=..."

# Response
{
  "users": [
    {
      "user_id": "user_192.168.1.1",
      "ip_address": "192.168.1.1",
      "request_count": 45,
      "status": "active",
      "first_seen": "2024-03-10T08:00:00",
      "last_seen": "2024-03-16T10:30:00"
    }
  ],
  "count": 1
}
```

### POST /admin/ban-user
**Ban a user**
```bash
curl -X POST http://localhost:5000/admin/ban-user \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"user_id":"user_192.168.1.1","reason":"Malicious activity"}'

# Response
{
  "success": true,
  "message": "User user_192.168.1.1 banned"
}
```

---

## 📊 Monitoring & Maintenance

### Database Maintenance
```python
# Clear old logs (older than 30 days)
from database import clear_old_logs
clear_old_logs(days=30)

# Get specific user history
from database import get_scan_history
history = get_scan_history(user_id="user_192.168.1.1")
```

### Performance Optimization
```python
# Add database indexes
# Already included in initialize_database()
# - idx_scan_results_time: for sorting by date
# - idx_scan_results_user: for user lookups
# - idx_users_status: for status filtering
```

### Audit Logging
All scans logged with:
- Timestamp (UTC)
- User ID
- IP Address
- URL analyzed
- Risk Score
- Detection Result

---

## 🎯 Next Steps

1. **Customize Admin Password**
   - Change in `app.py` line ~30: `ADMIN_PASSWORD = "your-new-password"`

2. **Add User Roles**
   - Create roles table
   - Add role hierarchy (admin, analyst, viewer)
   - Implement role-based access control

3. **Email Alerts**
   - Send alerts on high-risk detections
   - Daily/weekly reports

4. **Advanced Filtering**
   - Date range filtering
   - URL pattern search
   - Risk score range filtering
   - Source filtering

5. **Export Functionality**
   - CSV export of scans
   - PDF reports
   - Scheduled email delivery

6. **API Rate Limiting**
   - Prevent abuse
   - Per-user limits
   - IP-based limiting

7. **Two-Factor Authentication**
   - Add TOTP support
   - SMS verification
   - Backup codes

---

## 📞 Support

For issues or questions:
1. Check the ADMIN_PANEL.md documentation
2. Review backend logs: `python app.py`
3. Check frontend console: Browser DevTools
4. Check database: `frontend/phishguard.db`

---

## 📄 License

PhishGuard AI - Admin Panel
Part of the PhishGuard AI cybersecurity project
