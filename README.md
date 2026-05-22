# OsintHAM — OSINT Investigation Constructor

## 📋 Description

**OsintHAM** is an Open Source Intelligence (OSINT) investigation constructor — a web-based tool for building relationship graphs, collecting information from sources, and generating investigation reports.

## 🏗️ Architecture

### Lite Version (Current)
- **Manual node/edge creation** — investigator enters all data
- **Interactive graph visualization** — Cytoscape.js / react-force-graph
- **Report generation** — JSON, HTML, Markdown export
- **Web terminal** — xterm.js for manual OSINT commands
- **Questionnaire templates** — per node type

### Medium Version (Planned)
- Auto-enrichment: email → find social accounts
- Metadata pulling: WHOIS, DNS, basic OSINT
- Import from CSV/JSON

### Full Version (Future)
- Automated scanning across 50+ platforms
- Profile parsing, full relationship mapping
- Integration with Maigret, Sherlock, Holehe

## 📁 Project Structure

```
osintham/
├── backend/                 # FastAPI (Python)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI entry point
│   │   ├── models.py        # Data models
│   │   ├── database.py      # SQLite storage
│   │   ├── graph_engine.py  # Graph analysis (NetworkX)
│   │   ├── api/
│   │   │   ├── investigations.py  # CRUD investigations
│   │   │   ├── nodes.py           # Node operations
│   │   │   ├── edges.py           # Edge operations
│   │   │   ├── graph_api.py       # Graph queries
│   │   │   ├── reports.py         # Report generation
│   │   │   └── templates.py       # Questionnaire templates
│   │   └── schemas.py       # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # React (Vite)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Investigation list
│   │   │   ├── Investigation.jsx   # Workspace
│   │   │   ├── GraphView.jsx       # Graph visualization
│   │   │   ├── Reports.jsx         # Reports & export
│   │   │   └── TerminalPage.jsx    # Web terminal
│   │   ├── components/
│   │   │   ├── NodeEditor.jsx      # Node questionnaire
│   │   │   ├── EdgeEditor.jsx      # Edge editor
│   │   │   ├── TrustBadge.jsx      # Trust level indicator
│   │   │   └── LogPanel.jsx        # Action log
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docs/                    # Documentation
├── docker-compose.yml
├── LICENSE
└── README.md
```

## 🔧 Core Entities

### Node (Graph Node)
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier |
| type | enum | email, phone, person, organization, social_account, domain, ip, event, document |
| label | string | Display name |
| trust_level | int (1-5) | Rumor → Verified |
| data | JSON | Questionnaire fields |
| source | string | Information source |
| color | string | Display color |

### Edge (Graph Edge)
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier |
| from_node | string | Source node id |
| to_node | string | Target node id |
| label | string | Relationship type |
| trust_level | int (1-5) | Trust level |
| bidirectional | boolean | Two-way relationship |

### Investigation
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier |
| title | string | Investigation name |
| description | string | Details |
| status | enum | active, paused, closed |
| created_at | datetime | Creation date |

### Report
- Formats: JSON, HTML, Markdown, PDF
- Templates available

## 🛠️ Tools & Modules

| Module | Purpose |
|--------|---------|
| Graph Engine | NetworkX — path finding, centrality analysis, clustering |
| Report Generator | Jinja2 templates → HTML/PDF |
| Storage | SQLite via SQLAlchemy |
| API | FastAPI with auto-generated OpenAPI docs |
| Frontend | React 18 + Vite + TailwindCSS |
| Graph Viz | react-force-graph-2d / Cytoscape.js |
| Terminal | xterm.js over WebSocket |

## 🚀 Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up --build
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/investigations | List all |
| POST | /api/investigations | Create new |
| GET | /api/investigations/{id} | Get one |
| PUT | /api/investigations/{id} | Update |
| DELETE | /api/investigations/{id} | Delete |
| POST | /api/investigations/{id}/nodes | Add node |
| PUT | /api/nodes/{id} | Update node |
| DELETE | /api/nodes/{id} | Delete node |
| POST | /api/investigations/{id}/edges | Add edge |
| PUT | /api/edges/{id} | Update edge |
| DELETE | /api/edges/{id} | Delete edge |
| GET | /api/investigations/{id}/graph | Full graph data |
| GET | /api/investigations/{id}/report | Generate report |
| GET | /api/templates | List templates |

## 📓 Questionnaire Templates

Each node type has its own questionnaire:

**Person:** name, aliases, DOB, nationality, occupation, known_addresses, photo
**Email:** address, provider, linked_accounts, breach_history
**Phone:** number, carrier, country, linked_accounts
**Social Account:** platform, username, profile_url, activity_level
**Organization:** name, registration, website, key_persons, industry
**Domain:** domain, registrar, nameservers, registration_date, whois
**IP:** address, ISP, geolocation, ASN
**Event:** date, location, description, involved_parties
**Document:** title, source, date, content_summary, file_hash

## 🔒 Security & Ethics

- **Data stays local** — all data stored in local SQLite
- **No automated scraping** — investigator controls all input
- **Trust levels** — every piece of data is marked with confidence
- **Audit trail** — action log tracks all changes
- **Export control** — reports can be password-protected

## 📜 License

MIT License
