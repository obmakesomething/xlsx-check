"""Knowledge base management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database.connection import get_db
from database.schemas import KnowledgeEntryCreate, KnowledgeEntryOut
from services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/", response_model=list[KnowledgeEntryOut])
async def list_entries(
    category: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List knowledge entries."""
    svc = KnowledgeService(db)
    entries = await svc.list_entries(category=category, skip=skip, limit=limit)
    return entries


@router.post("/", response_model=KnowledgeEntryOut)
async def create_entry(
    data: KnowledgeEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge entry."""
    svc = KnowledgeService(db)
    entry = await svc.create_entry(
        category=data.category,
        title=data.title,
        content=data.content,
        source=data.source,
        tags=data.tags,
    )
    return entry


@router.get("/search")
async def search_knowledge(
    q: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    n_results: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Search the knowledge base."""
    svc = KnowledgeService(db)
    results = svc.search(q, category=category, n_results=n_results)
    return {"query": q, "results": results}


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all knowledge categories."""
    svc = KnowledgeService(db)
    categories = await svc.get_categories()
    return {"categories": categories}


@router.get("/{entry_id}", response_model=KnowledgeEntryOut)
async def get_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a knowledge entry by ID."""
    svc = KnowledgeService(db)
    entry = await svc.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry


@router.put("/{entry_id}", response_model=KnowledgeEntryOut)
async def update_entry(
    entry_id: int,
    data: KnowledgeEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update a knowledge entry."""
    svc = KnowledgeService(db)
    entry = await svc.update_entry(
        entry_id,
        category=data.category,
        title=data.title,
        content=data.content,
        source=data.source,
        tags=data.tags,
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge entry."""
    svc = KnowledgeService(db)
    deleted = await svc.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return {"detail": "Knowledge entry deleted"}
