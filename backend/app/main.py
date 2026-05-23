"""OsintHAM — FastAPI Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import init_db
from app.api import investigations, nodes, edges, graph_api, reports, templates, osint

# Initialize database
init_db()

app = FastAPI(
    title="OsintHAM",
    description="OSINT Investigation Constructor — graph-based investigation tool",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(investigations.router)
app.include_router(nodes.router)
app.include_router(edges.router)
app.include_router(graph_api.router)
app.include_router(reports.router)
app.include_router(templates.router)
app.include_router(osint.router)


# ── Serve Frontend (for production) ──
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "OsintHAM", "version": "0.2.0"}
