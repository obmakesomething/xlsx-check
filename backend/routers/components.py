"""Component management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database.connection import get_db
from database.schemas import ComponentCreate, ComponentUpdate, ComponentOut, SubstituteRequest
from services.component_service import ComponentService
from services.lcsc_service import LCSCService

router = APIRouter(prefix="/api/components", tags=["components"])


@router.get("/", response_model=list[ComponentOut])
async def list_components(
    project_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List components with optional filters."""
    svc = ComponentService(db)
    components = await svc.list_components(
        project_id=project_id,
        category=category,
        search=search,
        skip=skip,
        limit=limit,
    )
    return components


@router.post("/", response_model=ComponentOut)
async def create_component(
    data: ComponentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a new component."""
    svc = ComponentService(db)
    comp = await svc.create_component(**data.model_dump())
    return comp


@router.get("/search-lcsc")
async def search_lcsc(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Search LCSC for components."""
    result = await LCSCService.search(keyword, page=page, page_size=page_size)
    return result


@router.post("/substitute")
async def find_substitutes(
    data: SubstituteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Find substitute parts for a component."""
    svc = ComponentService(db)
    substitutes = await svc.find_substitutes(data.component_id, reason=data.reason)

    # Also try LCSC search for the component
    comp = await svc.get_component(data.component_id)
    lcsc_results = []
    if comp and comp.part_number:
        lcsc_data = await LCSCService.search(comp.part_number)
        if lcsc_data.get("success"):
            lcsc_results = lcsc_data.get("results", [])

    return {
        "component_id": data.component_id,
        "reason": data.reason,
        "rag_substitutes": substitutes,
        "lcsc_alternatives": lcsc_results,
    }


@router.get("/{component_id}", response_model=ComponentOut)
async def get_component(
    component_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a component by ID."""
    svc = ComponentService(db)
    comp = await svc.get_component(component_id)
    if comp is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return comp


@router.put("/{component_id}", response_model=ComponentOut)
async def update_component(
    component_id: int,
    data: ComponentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a component."""
    svc = ComponentService(db)
    update_data = data.model_dump(exclude_unset=True)
    comp = await svc.update_component(component_id, **update_data)
    if comp is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return comp


@router.delete("/{component_id}")
async def delete_component(
    component_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a component."""
    svc = ComponentService(db)
    deleted = await svc.delete_component(component_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Component not found")
    return {"detail": "Component deleted"}
