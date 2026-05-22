# OsintHAM — Deployment Guide

## Option 1: GitHub Pages (Static Frontend — Demo Mode)

This deploys the standalone `index.html` with localStorage-based data. No backend required.

### Steps:

1. **Create a new GitHub repository** (e.g., `osintham`)

2. **Upload the demo file:**
   ```bash
   cd /path/to/osintham
   git init
   git add index.html
   git commit -m "Initial commit — OsintHAM demo"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/osintham.git
   git push -u origin main
   ```

3. **Enable GitHub Pages:**
   - Go to repository → Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` / `root`
   - Click Save

4. **Access your deployment:**
   - URL: `https://YOUR_USERNAME.github.io/osintham`

### Features in Demo Mode:
- ✅ Create/manage investigations
- ✅ Add nodes (9 types) with questionnaire
- ✅ Add edges (relationships)
- ✅ Interactive graph (Cytoscape.js)
- ✅ Reports (JSON, HTML, Markdown export)
- ✅ Web terminal with 15+ commands
- ✅ Data persists in localStorage

---

## Option 2: Full Stack (Backend + Frontend)

### Docker Deployment:

```bash
cd osintham
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### Deploy to Railway / Render:

1. **Backend:**
   - Create new Web Service
   - Connect GitHub repo → `backend/` directory
   - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Frontend:**
   - Create new Static Site
   - Connect GitHub repo → `frontend/` directory
   - Build command: `npm run build`
   - Output directory: `dist`

---

## Option 3: GitHub Pages + External API

If you deploy the backend separately (e.g., on Railway), you can modify the frontend to use it:

1. In `frontend/src/api.js`, change:
   ```javascript
   const API_BASE = 'https://your-backend.railway.app/api'
   ```

2. Build and deploy:
   ```bash
   cd frontend
   npm run build
   # Upload dist/ to GitHub Pages
   ```

---

## Project Structure for GitHub

```
osintham/
├── index.html          ← GitHub Pages entry point (demo mode)
├── README.md
├── LICENSE
├── backend/            ← Full API (optional)
│   ├── app/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/           ← React app (optional)
│   ├── src/
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Updating

```bash
git add .
git commit -m "Update OsintHAM"
git push
# GitHub Pages auto-deploys in ~1 minute
```
