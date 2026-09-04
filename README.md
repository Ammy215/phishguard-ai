# PhishGuard AI

Real-time phishing URL detection combining a Random Forest ML classifier with a 16-rule heuristic engine, live threat-intel lookups (Google Safe Browsing, PhishTank, URLHaus), and an explainable-AI chat endpoint. Ships as a Flask API, a React dashboard, and a Chrome extension.

## Setup

**Backend**
```
cd backend
pip install -r requirements.txt
python app.py
```
Runs on `http://localhost:5000` by default — see `backend/.env.example` for config.

**Frontend**
```
cd frontend
npm install
npm run dev
```

**Chrome extension**
Load `chrome-extension/` as an unpacked extension via `chrome://extensions` (Developer mode). It talks to the backend on `localhost:5000` by default.

## Dataset

The ML classifier is trained on the [PhiUSIIL Phishing URL Dataset](https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset) (Prasad & Chandra, 2024, *Computers & Security*, DOI: 10.1016/j.cose.2023.103545) — 235,795 URLs (100,945 phishing / 134,850 legitimate).

The raw CSV isn't committed to this repo. To retrain, download it from UCI and place it at `backend/PhiUSIIL_Phishing_URL_Dataset.csv`, then run `backend/train_model.py`. The trained model (`backend/phish_model.joblib`) is already included and is what the app loads as-is.
