"""OsintHAM — Data Models and Database Layer"""
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./osintham.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class InvestigationModel(Base):
    __tablename__ = "investigations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, default="active")  # active, paused, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    nodes = relationship("NodeModel", back_populates="investigation", cascade="all, delete-orphan")
    edges = relationship("EdgeModel", back_populates="investigation", cascade="all, delete-orphan")


class NodeModel(Base):
    __tablename__ = "nodes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id"), nullable=False)
    type = Column(String, nullable=False)
    label = Column(String, nullable=False)
    trust_level = Column(Integer, default=3)
    data = Column(Text, default="{}")
    source = Column(String, default="")
    color = Column(String, default="#6366f1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    investigation = relationship("InvestigationModel", back_populates="nodes")


class EdgeModel(Base):
    __tablename__ = "edges"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id"), nullable=False)
    from_node = Column(String, nullable=False)
    to_node = Column(String, nullable=False)
    label = Column(String, default="")
    trust_level = Column(Integer, default=3)
    bidirectional = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    investigation = relationship("InvestigationModel", back_populates="edges")


class TemplateModel(Base):
    __tablename__ = "templates"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    node_type = Column(String, nullable=False)
    fields = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
