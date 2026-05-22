"""OsintHAM — Questionnaire Template API"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, TemplateModel
from app.schemas import TemplateCreate, TemplateResponse

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Default templates for each node type
DEFAULT_TEMPLATES = [
    {
        "name": "Person Profile",
        "node_type": "person",
        "fields": [
            {"name": "full_name", "label": "Full Name", "type": "text", "required": True},
            {"name": "aliases", "label": "Aliases / Nicknames", "type": "text"},
            {"name": "date_of_birth", "label": "Date of Birth", "type": "date"},
            {"name": "nationality", "label": "Nationality", "type": "text"},
            {"name": "occupation", "label": "Occupation", "type": "text"},
            {"name": "known_addresses", "label": "Known Addresses", "type": "textarea"},
            {"name": "photo_url", "label": "Photo URL", "type": "url"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
    {
        "name": "Email Address",
        "node_type": "email",
        "fields": [
            {"name": "email", "label": "Email Address", "type": "email", "required": True},
            {"name": "provider", "label": "Provider", "type": "text"},
            {"name": "linked_accounts", "label": "Linked Accounts", "type": "textarea"},
            {"name": "breach_history", "label": "Breach History", "type": "textarea"},
            {"name": "first_seen", "label": "First Seen", "type": "date"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
    {
        "name": "Phone Number",
        "node_type": "phone",
        "fields": [
            {"name": "number", "label": "Phone Number", "type": "tel", "required": True},
            {"name": "carrier", "label": "Carrier", "type": "text"},
            {"name": "country", "label": "Country", "type": "text"},
            {"name": "linked_accounts", "label": "Linked Accounts", "type": "textarea"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
    {
        "name": "Social Media Account",
        "node_type": "social_account",
        "fields": [
            {"name": "platform", "label": "Platform", "type": "text", "required": True},
            {"name": "username", "label": "Username", "type": "text", "required": True},
            {"name": "profile_url", "label": "Profile URL", "type": "url"},
            {"name": "activity_level", "label": "Activity Level", "type": "select", "options": ["active", "inactive", "abandoned", "unknown"]},
            {"name": "bio", "label": "Bio / Description", "type": "textarea"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
    {
        "name": "Organization",
        "node_type": "organization",
        "fields": [
            {"name": "name", "label": "Organization Name", "type": "text", "required": True},
            {"name": "registration", "label": "Registration Number", "type": "text"},
            {"name": "website", "label": "Website", "type": "url"},
            {"name": "industry", "label": "Industry", "type": "text"},
            {"name": "key_persons", "label": "Key Persons", "type": "textarea"},
            {"name": "address", "label": "Address", "type": "textarea"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
    {
        "name": "Domain",
        "node_type": "domain",
        "fields": [
            {"name": "domain", "label": "Domain Name", "type": "text", "required": True},
            {"name": "registrar", "label": "Registrar", "type": "text"},
            {"name": "nameservers", "label": "Nameservers", "type": "textarea"},
            {"name": "registration_date", "label": "Registration Date", "type": "date"},
            {"name": "expiry_date", "label": "Expiry Date", "type": "date"},
            {"name": "whois_data", "label": "WHOIS Data", "type": "textarea"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
    {
        "name": "IP Address",
        "node_type": "ip",
        "fields": [
            {"name": "address", "label": "IP Address", "type": "text", "required": True},
            {"name": "isp", "label": "ISP", "type": "text"},
            {"name": "geolocation", "label": "Geolocation", "type": "text"},
            {"name": "asn", "label": "ASN", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
    {
        "name": "Event",
        "node_type": "event",
        "fields": [
            {"name": "title", "label": "Event Title", "type": "text", "required": True},
            {"name": "date", "label": "Date", "type": "datetime-local"},
            {"name": "location", "label": "Location", "type": "text"},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "involved_parties", "label": "Involved Parties", "type": "textarea"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
    {
        "name": "Document",
        "node_type": "document",
        "fields": [
            {"name": "title", "label": "Document Title", "type": "text", "required": True},
            {"name": "source", "label": "Source", "type": "text"},
            {"name": "date", "label": "Date", "type": "date"},
            {"name": "content_summary", "label": "Content Summary", "type": "textarea"},
            {"name": "file_hash", "label": "File Hash (SHA-256)", "type": "text"},
            {"name": "file_url", "label": "File URL", "type": "url"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
]


@router.get("/", response_model=list[TemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    templates = db.query(TemplateModel).all()
    if not templates:
        # Seed default templates
        for t in DEFAULT_TEMPLATES:
            tmpl = TemplateModel(name=t["name"], node_type=t["node_type"], fields=json.dumps(t["fields"]))
            db.add(tmpl)
        db.commit()
        templates = db.query(TemplateModel).all()

    result = []
    for t in templates:
        result.append({
            "id": t.id,
            "name": t.name,
            "node_type": t.node_type,
            "fields": json.loads(t.fields) if t.fields else [],
            "created_at": t.created_at,
        })
    return result


@router.get("/{node_type}", response_model=TemplateResponse)
def get_template_by_type(node_type: str, db: Session = Depends(get_db)):
    tmpl = db.query(TemplateModel).filter(TemplateModel.node_type == node_type).first()
    if not tmpl:
        # Find in defaults
        for t in DEFAULT_TEMPLATES:
            if t["node_type"] == node_type:
                return {
                    "id": "default",
                    "name": t["name"],
                    "node_type": t["node_type"],
                    "fields": t["fields"],
                    "created_at": None,
                }
        raise HTTPException(status_code=404, detail=f"No template for type: {node_type}")
    return {
        "id": tmpl.id,
        "name": tmpl.name,
        "node_type": tmpl.node_type,
        "fields": json.loads(tmpl.fields) if tmpl.fields else [],
        "created_at": tmpl.created_at,
    }


@router.post("/", response_model=TemplateResponse)
def create_template(req: TemplateCreate, db: Session = Depends(get_db)):
    tmpl = TemplateModel(name=req.name, node_type=req.node_type, fields=json.dumps(req.fields))
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return {
        "id": tmpl.id,
        "name": tmpl.name,
        "node_type": tmpl.node_type,
        "fields": json.loads(tmpl.fields) if tmpl.fields else [],
        "created_at": tmpl.created_at,
    }
