"""OsintHAM — Edge API Router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, EdgeModel
from app.schemas import EdgeCreate, EdgeUpdate, EdgeResponse

router = APIRouter(prefix="/api", tags=["edges"])


@router.post("/investigations/{inv_id}/edges", response_model=EdgeResponse)
def create_edge(inv_id: str, req: EdgeCreate, db: Session = Depends(get_db)):
    edge = EdgeModel(
        investigation_id=inv_id,
        from_node=req.from_node,
        to_node=req.to_node,
        label=req.label,
        trust_level=req.trust_level,
        bidirectional=req.bidirectional,
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return _edge_response(edge)


@router.get("/edges/{edge_id}", response_model=EdgeResponse)
def get_edge(edge_id: str, db: Session = Depends(get_db)):
    edge = db.query(EdgeModel).filter(EdgeModel.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    return _edge_response(edge)


@router.put("/edges/{edge_id}", response_model=EdgeResponse)
def update_edge(edge_id: str, req: EdgeUpdate, db: Session = Depends(get_db)):
    edge = db.query(EdgeModel).filter(EdgeModel.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    if req.from_node is not None:
        edge.from_node = req.from_node
    if req.to_node is not None:
        edge.to_node = req.to_node
    if req.label is not None:
        edge.label = req.label
    if req.trust_level is not None:
        edge.trust_level = req.trust_level
    if req.bidirectional is not None:
        edge.bidirectional = req.bidirectional
    db.commit()
    db.refresh(edge)
    return _edge_response(edge)


@router.delete("/edges/{edge_id}")
def delete_edge(edge_id: str, db: Session = Depends(get_db)):
    edge = db.query(EdgeModel).filter(EdgeModel.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    db.delete(edge)
    db.commit()
    return {"status": "deleted", "id": edge_id}


def _edge_response(edge: EdgeModel) -> dict:
    return {
        "id": edge.id,
        "investigation_id": edge.investigation_id,
        "from_node": edge.from_node,
        "to_node": edge.to_node,
        "label": edge.label,
        "trust_level": edge.trust_level,
        "bidirectional": edge.bidirectional,
        "created_at": edge.created_at,
    }
