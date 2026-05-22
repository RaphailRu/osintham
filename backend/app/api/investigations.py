"""OsintHAM — Investigation API Router"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, InvestigationModel
from app.schemas import InvestigationCreate, InvestigationUpdate, InvestigationResponse

router = APIRouter(prefix="/api/investigations", tags=["investigations"])


@router.get("/", response_model=list[InvestigationResponse])
def list_investigations(db: Session = Depends(get_db)):
    investigations = db.query(InvestigationModel).order_by(InvestigationModel.updated_at.desc()).all()
    result = []
    for inv in investigations:
        result.append({
            "id": inv.id,
            "title": inv.title,
            "description": inv.description,
            "status": inv.status,
            "created_at": inv.created_at,
            "updated_at": inv.updated_at,
            "node_count": len(inv.nodes),
            "edge_count": len(inv.edges),
        })
    return result


@router.post("/", response_model=InvestigationResponse)
def create_investigation(req: InvestigationCreate, db: Session = Depends(get_db)):
    inv = InvestigationModel(title=req.title, description=req.description)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return {
        "id": inv.id,
        "title": inv.title,
        "description": inv.description,
        "status": inv.status,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "node_count": 0,
        "edge_count": 0,
    }


@router.get("/{inv_id}", response_model=InvestigationResponse)
def get_investigation(inv_id: str, db: Session = Depends(get_db)):
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {
        "id": inv.id,
        "title": inv.title,
        "description": inv.description,
        "status": inv.status,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "node_count": len(inv.nodes),
        "edge_count": len(inv.edges),
    }


@router.put("/{inv_id}", response_model=InvestigationResponse)
def update_investigation(inv_id: str, req: InvestigationUpdate, db: Session = Depends(get_db)):
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    if req.title is not None:
        inv.title = req.title
    if req.description is not None:
        inv.description = req.description
    if req.status is not None:
        inv.status = req.status
    db.commit()
    db.refresh(inv)
    return {
        "id": inv.id,
        "title": inv.title,
        "description": inv.description,
        "status": inv.status,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "node_count": len(inv.nodes),
        "edge_count": len(inv.edges),
    }


@router.delete("/{inv_id}")
def delete_investigation(inv_id: str, db: Session = Depends(get_db)):
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    db.delete(inv)
    db.commit()
    return {"status": "deleted", "id": inv_id}
