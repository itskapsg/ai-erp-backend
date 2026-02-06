# PROJECT CONTEXT: JGandhi Tex ERP

## 1. System Architecture (Hybrid Stable)
- **Server:** VPS (Ubuntu 24.04), IP: 95.111.253.134
- **Process Manager:** PM2 (Native) manages Backend (54279) & Frontend (56000).
- **Agent:** Gemini Operator (Native Python) runs via `operator.py`.
- **Backend:** FastAPI (Port 54279). Dependencies installed in `venv`.
- **Frontend:** React/Vite (Port 56000). Public access via 0.0.0.0.

## 2. Recent Achievements
- **Rescue Mission:** Fixed "Login Loop" by hardcoding `VITE_API_URL`.
- **Rescue Mission:** Fixed "Backend Crash" by installing `python-multipart` and `python-jose`.
- **Namaste UI:** Created `frontend/src/pages/Namaste.jsx` with:
  - Dashboard (Active Visits Cards).
  - Wizard Dialog (3 Steps: Who, Logistics, Food).
  - Integration with `namasteAPI`.

## 3. Current Task: Wiring it Up
- **Goal:** Make the Namaste page accessible in the app.
- **TODO:**
  1. Update `frontend/src/App.jsx`: Add Route `/namaste`.
  2. Update `frontend/src/layouts/MainLayout.jsx`: Add Sidebar Link with Handshake Icon.
