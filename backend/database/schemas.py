"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ── Project ──────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    spec: dict[str, Any] = {}
    status: str = "draft"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    spec: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class ComponentOut(BaseModel):
    id: int
    project_id: int
    ref_designator: str
    part_number: str
    manufacturer: str
    description: str
    package: str
    quantity: int
    unit_price: float
    lcsc_code: str
    category: str
    properties: dict[str, Any]

    model_config = {"from_attributes": True}


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    spec: dict[str, Any]
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    components: list[ComponentOut] = []

    model_config = {"from_attributes": True}


class ProjectListOut(BaseModel):
    id: int
    name: str
    description: str
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Component ────────────────────────────────────────────────────────────────

class ComponentCreate(BaseModel):
    project_id: int
    ref_designator: str = ""
    part_number: str = ""
    manufacturer: str = ""
    description: str = ""
    package: str = ""
    quantity: int = 1
    unit_price: float = 0.0
    lcsc_code: str = ""
    category: str = ""
    properties: dict[str, Any] = {}


class ComponentUpdate(BaseModel):
    ref_designator: Optional[str] = None
    part_number: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    package: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    lcsc_code: Optional[str] = None
    category: Optional[str] = None
    properties: Optional[dict[str, Any]] = None


# ── Knowledge ────────────────────────────────────────────────────────────────

class KnowledgeEntryCreate(BaseModel):
    category: str
    title: str
    content: str
    source: str = ""
    tags: list[str] = []


class KnowledgeEntryUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[list[str]] = None


class KnowledgeEntryOut(BaseModel):
    id: int
    category: str
    title: str
    content: str
    source: str
    tags: list[str]
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    project_id: Optional[int] = None
    context: dict[str, Any] = {}


class ChatMessageOut(BaseModel):
    id: int
    project_id: Optional[int]
    role: str
    content: str
    agent_type: str
    metadata: dict[str, Any]
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Copilot Analyze ──────────────────────────────────────────────────────────

class CopilotAnalyzeRequest(BaseModel):
    user_request: str
    project_spec: dict[str, Any] = {}
    file_bundle_summary: dict[str, Any] = {}
    bom_data: list[dict[str, Any]] = []
    previous_context: list[dict[str, Any]] = []
    project_id: Optional[int] = None


class SubstituteRequest(BaseModel):
    project_id: int
    component_id: int
    reason: str = "cost_reduction"


# ── Circuit Block ────────────────────────────────────────────────────────────

class CircuitBlockOut(BaseModel):
    id: int
    project_id: int
    name: str
    block_type: str
    components: list[Any]
    description: str

    model_config = {"from_attributes": True}


# ── Design History ───────────────────────────────────────────────────────────

class DesignHistoryOut(BaseModel):
    id: int
    project_id: int
    action: str
    details: dict[str, Any]
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
