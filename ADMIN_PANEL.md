# PhishGuard AI - Admin Panel Documentation

## Overview

The Admin Panel is a professional Security Operations Center (SOC) dashboard for monitoring phishing detections, managing users, and tracking system health in real-time.

## Features

### 🔐 Authentication
- **Secure Login**: Admin credentials required to access dashboard
- **Session Management**: Flask sessions protect sensitive data
- **Demo Credentials**:
  - Username: `admin`
  - Password: `phishguard123`

### 📊 System Statistics
Dashboard displays real-time metrics:
- **Total Scans**: Cumulative count of all analyzed URLs
- **Phishing Detections**: Number of malicious URLs identified
- **Safe URLs**: Legitimate websites passed
- **Active Users**: Connected users currently using the system
- **System Status**: Operational indicator

### 📈 Detection Trends
Interactive chart showing detection patterns over the last 7 days:
- **Phishing Detections** (red bars): Malicious URLs detected
- **Safe Detections** (green bars): Legitimate URLs verified

### 🔍 Threat Intelligence Status
Real-time status of all threat feeds:
- **PhishTank**: 56,486+ URLs updated daily
- **OpenPhish**: 300+ URLs monitored
- **Google Safe Browsing**: Real-time threat data
- **ML Model**: Random Forest classifier with 16+ heuristics

### 📋 Recent Scans
Live table of latest URL analysis:
- **URL**: Analyzed website
- **Risk Score**: 0-100% threat probability
- **Result**: PHISHING or SAFE
- **Source**: Extension or Dashboard
- **Time**: When scan occurred

### 👥 User Management
- **View Users**: All connected users and their activity
- **Request Count**: Scans performed by each user
- **Status**: Active or Banned
- **Ban Users**: Prevent malicious users from accessing system
- **Ban History**: Track and manage banned users

## Architecture

### Backend (Flask)
Located in: `backend/app.py` and `backend/database.py`

#### Database Schema

**scan_results**
```sql
- id (Primary Key)
- url
- risk_score
- result (SAFE/PHISHING)
- scan_time
- source (extension/dashboard)
- user_id
- ip_address
```

**users**
```sql
- user_id (Primary Key)
- ip_address
- request_count
- status (active/banned)
- first_seen
- last_seen
```

**banned_users**
```sql
- id (Primary Key)
- user_id
- ip_address
- ban_time
- reason
```

#### Admin Endpoints

##### Authentication
```
POST /admin
  - username: string
  - password: string
  Response: { success: boolean, message: string }

POST /admin/logout
  Response: { success: boolean, message: string }
```

##### Statistics
```
GET /admin/stats (requires auth)
  Response: {
    total_scans: number,
    phishing_detections: number,
    safe_detections: number,
    active_users: number,
    system_status: string
  }

GET /admin/detection-stats (requires auth)
  Response: {
    stats: [
      { result: string, count: number, date: string }
    ]
  }
```

##### Scan Data
```
GET /admin/recent-scans?limit=50 (requires auth)
  Response: {
    scans: [ scan_result_objects ],
    count: number
  }
```

##### User Management
```
GET /admin/users?limit=100 (requires auth)
  Response: { users: [ user_objects ], count: number }

GET /admin/banned-users?limit=100 (requires auth)
  Response: { banned_users: [ banned_user_objects ], count: number }

POST /admin/ban-user (requires auth)
  - user_id: string
  - reason: string (optional)
  Response: { success: boolean, message: string }

POST /admin/unban-user (requires auth)
  - user_id: string
  Response: { success: boolean, message: string }
```

### Frontend (React + TypeScript)
Located in: `frontend/src/admin/`

#### Directory Structure
```
frontend/src/admin/
├── index.ts              # Exports
├── pages/
│   ├── login.tsx        # Login page
│   └── dashboard.tsx    # Main dashboard
└── components/
    ├── stats-cards.tsx           # Statistics display
    ├── detection-chart.tsx       # 7-day trend chart
    ├── recent-scans-table.tsx    # Scan history
    ├── users-table.tsx           # User management
    ├── banned-users.tsx          # Banned users list
    └── threat-status.tsx         # Threat feed status
```

#### Components

**StatsCards**
- Displays 5 metric cards
- Real-time updates
- Color-coded for easy scanning

**DetectionChart**
- Uses Recharts library
- Shows 7-day trend
- Phishing vs Safe breakdown

**RecentScansTable**
- Last 50 scans
- Sortable columns
- Risk score color coding
- Source indicator (extension/dashboard)

**UsersTable**
- Active user list
- Request count
- Ban functionality
- IP address tracking

**BannedUsers**
- Banned user list
- Ban reason display
- Unban functionality
- Ban timestamp

**ThreatStatus**
- Feed status indicators
- All systems show ACTIVE
- Description for each feed
- Last update timestamp

## Usage

### Accessing Admin Panel

1. **Start Backend**
   ```bash
   cd backend
   python app.py
   ```
   Backend runs on http://localhost:5000 by default

2. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend runs on http://localhost:5173 by default

3. **Navigate to Admin**
   - Open browser
   - Go to: http://localhost:5173/admin
   - Or: http://localhost:5173/admin/login

4. **Login**
   - Username: `admin`
   - Password: `phishguard123`

### Monitoring

#### Real-time Metrics
- Dashboard auto-refreshes every 30 seconds
- Manual refresh button available
- All data pulled from live database

#### User Tracking
- Each request updates user last_seen timestamp
- Request count increments per scan
- New users auto-created on first request

#### Ban Management
- Ban user to block all requests
- Banned users: HTTP 403 "User is banned"
- Unban to restore access

## Security Features

### 1. Session Management
- Flask secure session cookies
- Session-only auth duration
- Logout clears session

### 2. Request Validation
- Admin decorator checks session
- 401 Unauthorized if not logged in
- CORS credentials required

### 3. IP Tracking
- All requests logged with IP
- User activity history
- Incident investigation support

### 4. User Banning
- Prevents malicious users
- Blocks at API level
- Ban history maintained

## Database Management

### Initialization
```python
from database import initialize_database
initialize_database()  # Creates tables on first run
```

### Logging Scans
```python
from database import log_scan_result
log_scan_result(
    url="https://example.com",
    risk_score=65.5,
    result="PHISHING",
    source="extension",
    user_id="user123",
    ip_address="192.168.1.1"
)
```

### User Tracking
```python
from database import track_user, is_user_banned
track_user("user123", "192.168.1.1")
is_banned = is_user_banned("user123")
```

### Admin Actions
```python
from database import (
    ban_user, unban_user, get_stats,
    get_recent_scans, get_users
)

ban_user("user123", reason="Malicious activity")
unban_user("user123")
stats = get_stats()
```

## Configuration

### Backend (.env)
```bash
PORT=5000
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=*
```

### Frontend (vite.config.ts)
Backend API URL: `http://localhost:5000`

## Dark Mode Support

Admin panel includes automatic dark mode:
- Inherits from system theme
- Uses Tailwind dark utilities
- All components fully themed

## Performance Considerations

### Database
- Indexes on frequently queried columns
- TTL-based cache in backend
- Threadsafe database access

### Frontend
- Component lazy loading
- Efficient data fetching
- 30-second refresh interval
- Pagination support (limit parameters)

## Troubleshooting

### Login Issues
- Verify backend is running on port 5000
- Check credentials: admin / phishguard123
- Clear browser cache/cookies
- Check browser console for CORS errors

### No Data Appearing
- Verify /predict endpoint has been called
- Database should auto-initialize
- Check browser network tab for API responses
- Ensure 30-second refresh or manual refresh

### User Banning Not Working
- Verify user_id format matches
- Check database for ban entry
- Restart backend for session cache clear

### Database Issues
- Check phishguard.db exists in backend/
- Verify write permissions to backend/
- Delete phishguard.db to reset database
- Check app.py logs for SQL errors

## Future Enhancements

- [ ] User role management (admin, analyst, viewer)
- [ ] Export reports (CSV, PDF)
- [ ] Custom date range for statistics
- [ ] Email alerts for PHISHING detection
- [ ] API rate limiting per user
- [ ] Advanced filtering and search
- [ ] Threat feed configuration UI
- [ ] Model retraining interface
- [ ] Audit logs for admin actions
- [ ] Two-factor authentication

## API Rate Limiting

Current implementation: No rate limiting

To add rate limiting:
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

@app.route("/predict", methods=["POST"])
@limiter.limit("100 per hour")
def predict():
    # ...
```

## Compliance & Audit

All scans are logged with:
- Timestamp (UTC)
- Source (extension/dashboard)
- URL analyzed
- Risk score
- Result
- User ID
- IP address

This enables:
- Security incident investigation
- Usage analytics
- Compliance reporting
- User behavior analysis
