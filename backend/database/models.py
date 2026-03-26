"""SQLAlchemy ORM models for the LED Copilot system."""

import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, default="")
    spec = Column(JSON, default=dict)
    status = Column(String(50), default="draft", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    components = relationship("Component", back_populates="project", cascade="all, delete-orphan")
    circuit_blocks = relationship("CircuitBlock", back_populates="project", cascade="all, delete-orphan")
    design_history = relationship("DesignHistory", back_populates="project", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="project", cascade="all, delete-orphan")


class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    ref_designator = Column(String(50), default="")
    part_number = Column(String(100), default="", index=True)
    manufacturer = Column(String(200), default="")
    description = Column(Text, default="")
    package = Column(String(50), default="")
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    lcsc_code = Column(String(50), default="")
    category = Column(String(100), default="")
    properties = Column(JSON, default=dict)

    project = relationship("Project", back_populates="components")


class CircuitBlock(Base):
    __tablename__ = "circuit_blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    block_type = Column(String(100), default="")
    components = Column(JSON, default=list)
    description = Column(Text, default="")

    project = relationship("Project", back_populates="circuit_blocks")


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500), default="")
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DesignHistory(Base):
    __tablename__ = "design_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="design_history")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    agent_type = Column(String(50), default="orchestrator")
    meta_info = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="chat_messages")
