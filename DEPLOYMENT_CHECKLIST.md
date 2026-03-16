# PhishGuard AI - Safe Browsing API Fix & Deployment Checklist

## 🔧 What Was Fixed

✅ **Environment Variable Loading** - Now accepts both `GOOGLE_SAFE_BROWSING_API_KEY` and `GOOGLE_SAFE_BROWSING_KEY`
✅ **Missing Threat Type** - Added `POTENTIALLY_HARMFUL_APPLICATION` 
✅ **Error Handling** - 8 specific error handlers instead of generic
✅ **Logging** - Enhanced debugging with detailed error messages
✅ **Documentation** - 5 new guide files for setup and troubleshooting

---

## 📋 Deployment Checklist

### Phase 1: Local Testing (Backend)

- [ ] Navigate to backend directory
  ```bash
  cd backend
  ```

- [ ] Copy environment template
  ```bash
  cp .env.example .env
  ```

- [ ] Open `.env` and add your Google Safe Browsing API key
  ```
  GOOGLE_SAFE_BROWSING_API_KEY=YOUR_API_KEY_HERE
  ```
  OR
  ```
  GOOGLE_SAFE_BROWSING_KEY=YOUR_API_KEY_HERE
  ```

- [ ] Run diagnostic script
  ```bash
  python test_safe_browsing.py
  ```
  Expected output:
  ```
  ✓ API key loaded successfully
  ✓ Connection successful (HTTP 200)
  ✓ Clean
  ```

- [ ] Start backend server
  ```bash
  python app.py
  ```

---

### Phase 2: Local Testing (Frontend)

- [ ] Navigate to frontend directory
  ```bash
  cd frontend
  ```

- [ ] Start dev server
  ```bash
  npm run dev
  ```

- [ ] Access admin panel
  ```
  http://localhost:5173/admin
  Login: admin / phishguard123
  ```

- [ ] Verify dashboard loads

---

### Phase 3: Integration Testing

- [ ] Open admin dashboard in browser
- [ ] Go to Scanner page (or use Chrome extension)
- [ ] Test with safe URL: `https://www.google.com`
- [ ] Verify result shows in Recent Scans table
- [ ] Test with suspicious URL (if available)
- [ ] Check logs for Safe Browsing checks

---

### Phase 4: Render Deployment (Backend)

- [ ] Create Render account (free tier available)
  ```
  https://render.com
  ```

- [ ] Create new Web Service
  - Connect GitHub repo (or upload ZIP)
  - Select Python environment
  - Build command: `pip install -r requirements.txt`
  - Start command: `python app.py`

- [ ] Add environment variables in Render dashboard
  - Go to: Dashboard → Your Service → Environment
  - Add: `GOOGLE_SAFE_BROWSING_API_KEY=YOUR_KEY`
  - Add: `PORT=5000` (default for Render)
  - Add: `FLASK_ENV=production`
  - Add: `FLASK_DEBUG=false`

- [ ] Deploy backend
  - Push to GitHub or manual deploy
  - Wait for build to complete
  - Verify health endpoint:
    ```
    https://your-backend.onrender.com/health
    ```

---

### Phase 5: Vercel Deployment (Frontend)

- [ ] Create Vercel account (free tier)
  ```
  https://vercel.com
  ```

- [ ] Import project from GitHub
  - Select frontend folder
  - Framework: Vite
  - Build command: `npm run build`
  - Output directory: `dist`

- [ ] Add environment variables
  - `VITE_API_URL=https://your-backend.onrender.com`

- [ ] Deploy
  - Vercel will build and deploy automatically
  - Get deployment URL from dashboard

---

### Phase 6: Chrome Extension Configuration

- [ ] Update extension to use Render backend
  - Open `chrome-extension/background.js` (or wherever API calls are made)
  - Change: `const API_URL = 'http://localhost:5000'`
  - To: `const API_URL = 'https://your-backend.onrender.com'`

- [ ] Update CORS in app.py (if needed)
  ```python
  # In app.py, add your domains:
  "origins": [
      "https://your-frontend.vercel.app",
      "chrome-extension://YOUR_EXTENSION_ID"
  ]
  ```

- [ ] Update manifest.json
  - Add permissions for your backend domain
  - Example: `"host_permissions": ["https://your-backend.onrender.com/*"]`

- [ ] Build extension ZIP
  - Package chrome-extension folder
  - Share with beta testers

---

### Phase 7: Final Verification

- [ ] Backend Health Check
  ```bash
  curl https://your-backend.onrender.com/health
  ```
  Expected: `{"status": "ok", "version": "3.0.0"}`

- [ ] Frontend Loads
  ```
  https://your-frontend.vercel.app/admin
  ```

- [ ] Login Works
  - Username: `admin`
  - Password: `phishguard123`

- [ ] Test Scan
  - Use Chrome extension to scan URL
  - Verify it appears in Recent Scans
  - Check detection chart updates

- [ ] Safe Browsing Works
  - Check logs for Safe Browsing requests
  - Verify API responses are logged
  - Test with URL from test_safe_browsing.py

---

## 🚨 Important Notes

### Rendering Database Issue
⚠️ **SQLite on Render won't persist data!**

For production, you need to migrate to PostgreSQL:

1. Create PostgreSQL database on Render
   - Add new PostgreSQL service in Render (free tier available)
   - Get connection string

2. Update database.py to use PostgreSQL instead of SQLite
   ```python
   # Change from: sqlite:///phish_guard.db
   # To: postgresql://user:pass@host/db
   ```

3. Install PostgreSQL driver
   ```bash
   pip install psycopg2
   ```

For now, data will reset when Render restarts. This is fine for beta testing.

### API Key Security
- ❌ Never commit .env to GitHub
- ✅ Use Render's environment variables
- ✅ Rotate API key regularly
- ✅ Monitor API usage in Google Cloud

---

## 📚 Documentation Files

All new documentation is in `backend/`:

1. **QUICK_FIX.md** - Quick reference (start here)
2. **SAFE_BROWSING_FIX.md** - Complete troubleshooting
3. **SAFE_BROWSING_SUMMARY.md** - Summary of changes
4. **CODE_CHANGES.md** - Before/after code comparison
5. **.env.example** - Configuration template

---

## 🧪 Testing Endpoints

After deployment, test these endpoints:

```bash
# Health check
GET https://your-backend.onrender.com/health

# Scan a URL
POST https://your-backend.onrender.com/predict
Content-Type: application/json
{
  "url": "https://www.google.com",
  "user_id": "test_user"
}

# Get detection stats (requires admin login)
GET https://your-backend.onrender.com/admin/detection-stats
# Configure session cookie for admin auth
```

---

## ✅ Success Criteria

All of these should be true before going live:

- [ ] Backend running on Render without errors
- [ ] Frontend deployed on Vercel and loads
- [ ] Admin login works
- [ ] Chrome extension can reach backend
- [ ] Scan results appear in admin dashboard
- [ ] Safe Browsing API checks are happening
- [ ] Database logs scan results (until Render restart)
- [ ] No 403 errors from Safe Browsing

---

## 🚀 Go Live

Once all checks pass:

1. **Test with friends**
   - Share Chrome extension ZIP
   - Have them scan URLs
   - Monitor admin dashboard

2. **Monitor logs**
   - Check for any integration issues
   - Watch Safe Browsing API responses

3. **Collect feedback**
   - User experience
   - Accuracy of detections
   - Performance

4. **Plan next improvements**
   - PostgreSQL migration
   - UI updates
   - Feature additions

---

## 🆘 If Something Goes Wrong

### Backend won't start
```bash
python test_safe_browsing.py  # Check API key
pip install -r requirements.txt  # Verify deps
python app.py  # Check logs
```

### Safe Browsing not working
```bash
python test_safe_browsing.py  # Run diagnostic
# Check error messages and follow recommendations
```

### Frontend not connecting to backend
- Check CORS configuration in app.py
- Verify backend URL in frontend
- Check browser console for errors

### Database not persisting
- Expected on Render with SQLite
- Plan PostgreSQL migration for production

---

## 📞 Quick Support

- Check **SAFE_BROWSING_FIX.md** for detailed troubleshooting
- Run **test_safe_browsing.py** for diagnostic info
- Read **CODE_CHANGES.md** to understand modifications
- Review logs: `python app.py` to see detailed errors

---

## 🎯 Summary

✅ Safe Browsing API integration fixed and enhanced
✅ Ready for local testing
✅ Ready for Render deployment
✅ Ready for Vercel deployment  
✅ Complete documentation provided
✅ Diagnostic tools included

**You're ready to deploy!** 🚀
