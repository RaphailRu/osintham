"""OsintHAM — Node API Router"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, NodeModel
from app.schemas import NodeCreate, NodeUpdate, NodeResponse

router = APIRouter(prefix="/api", tags=["nodes"])


@router.post("/investigations/{inv_id}/nodes", response_model=NodeResponse)
def create_node(inv_id: str, req: NodeCreate, db: Session = Depends(get_db)):
    node = NodeModel(
        investigation_id=inv_id,
        type=req.type,
        label=req.label,
        trust_level=req.trust_level,
        data=json.dumps(req.data),
        source=req.source,
        color=req.color,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return _node_response(node)


@router.get("/nodes/{node_id}", response_model=NodeResponse)
def get_node(node_id: str, db: Session = Depends(get_db)):
    node = db.query(NodeModel).filter(NodeModel.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return _node_response(node)


@router.put("/nodes/{node_id}", response_model=NodeResponse)
def update_node(node_id: str, req: NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(NodeModel).filter(NodeModel.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if req.type is not None:
        node.type = req.type
    if req.label is not None:
        node.label = req.label
    if req.trust_level is not None:
        node.trust_level = req.trust_level
    if req.data is not None:
        node.data = json.dumps(req.data)
    if req.source is not None:
        node.source = req.source
    if req.color is not None:
        node.color = req.color
    db.commit()
    db.refresh(node)
    return _node_response(node)


@router.delete("/nodes/{node_id}")
def delete_node(node_id: str, db: Session = Depends(get_db)):
    node = db.query(NodeModel).filter(NodeModel.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    db.commit()
    return {"status": "deleted", "id": node_id}


def _node_response(node: NodeModel) -> dict:
    return {
        "id": node.id,
        "investigation_id": node.investigation_id,
        "type": node.type,
        "label": node.label,
        "trust_level": node.trust_level,
        "data": json.loads(node.data) if node.data else {},
        "source": node.source,
        "color": node.color,
        "created_at": node.created_at,
        "updated_at": node.updated_at,
    }
