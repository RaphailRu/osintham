"""OsintHAM — Pydantic Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ── Node Schemas ──

class NodeCreate(BaseModel):
    type: str = Field(..., description="Node type: email, phone, person, organization, social_account, domain, ip, event, document")
    label: str = Field(..., description="Display name")
    trust_level: int = Field(default=3, ge=1, le=5)
    data: dict = Field(default_factory=dict)
    source: str = ""
    color: str = "#6366f1"


class NodeUpdate(BaseModel):
    type: Optional[str] = None
    label: Optional[str] = None
    trust_level: Optional[int] = Field(default=None, ge=1, le=5)
    data: Optional[dict] = None
    source: Optional[str] = None
    color: Optional[str] = None


class NodeResponse(BaseModel):
    id: str
    investigation_id: str
    type: str
    label: str
    trust_level: int
    data: dict
    source: str
    color: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Edge Schemas ──

class EdgeCreate(BaseModel):
    from_node: str
    to_node: str
    label: str = ""
    trust_level: int = Field(default=3, ge=1, le=5)
    bidirectional: bool = False


class EdgeUpdate(BaseModel):
    from_node: Optional[str] = None
    to_node: Optional[str] = None
    label: Optional[str] = None
    trust_level: Optional[int] = Field(default=None, ge=1, le=5)
    bidirectional: Optional[bool] = None


class EdgeResponse(BaseModel):
    id: str
    investigation_id: str
    from_node: str
    to_node: str
    label: str
    trust_level: int
    bidirectional: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Investigation Schemas ──

class InvestigationCreate(BaseModel):
    title: str
    description: str = ""


class InvestigationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class InvestigationResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    node_count: int = 0
    edge_count: int = 0

    class Config:
        from_attributes = True


# ── Graph Export ──

class GraphData(BaseModel):
    nodes: list[dict]
    edges: list[dict]
    stats: dict = {}


# ── Template Schemas ──

class TemplateCreate(BaseModel):
    name: str
    node_type: str
    fields: list[dict] = []


class TemplateResponse(BaseModel):
    id: str
    name: str
    node_type: str
    fields: list[dict]
    created_at: datetime

    class Config:
        from_attributes = True
