"""OsintHAM — FastAPI Main Application v3"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import init_db
from app.api import investigations, nodes, edges, graph_api, reports, templates, osint, agents

init_db()

app = FastAPI(
    title="OsintHAM",
    description="OSINT Investigation Constructor — graph-based investigation tool with 25+ OSINT integrations",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigations.router)
app.include_router(nodes.router)
app.include_router(edges.router)
app.include_router(graph_api.router)
app.include_router(reports.router)
app.include_router(templates.router)
app.include_router(osint.router)
app.include_router(agents.router)

# Serve frontend
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
    return {"status": "ok", "service": "OsintHAM", "version": "0.3.0"}


@app.get("/api")
def api_root():
    return {
        "service": "OsintHAM",
        "version": "0.3.0",
        "endpoints": {
            "investigations": "/api/investigations",
            "nodes": "/api/nodes",
            "edges": "/api/edges",
            "graph": "/api/investigations/{id}/graph",
            "reports": "/api/investigations/{id}/report",
            "templates": "/api/templates",
            "osint": {
                "scan": "POST /api/osint/scan",
                "email": "/api/osint/email/{email}",
                "phone": "/api/osint/phone/{phone}",
                "domain": "/api/osint/domain/{domain}",
                "ip": "/api/osint/ip/{ip}",
                "username": "/api/osint/username/{username}",
                "url": "/api/osint/url?url=",
                "wayback": "/api/osint/wayback?domain=",
                "shodan": "/api/osint/shodan?ip=",
                "ghdb": "/api/osint/ghdb/{domain}",
                "geolocation": "/api/osint/geolocation?query=",
                "universal": "/api/osint/universal/{query}",
                "hash": "/api/osint/hash/{text}",
                "enrich": "POST /api/osint/enrich/{inv_id}",
                "tools": "/api/osint/tools",
            },
            "agents": {
                "investigate": "POST /api/agents/investigate",
                "status": "GET /api/agents/status/{id}",
                "result": "GET /api/agents/result/{id}",
                "cancel": "DELETE /api/agents/cancel/{id}",
                "scanners": "GET /api/agents/scanners",
                "health": "GET /api/agents/health",
            },
        },
    }
