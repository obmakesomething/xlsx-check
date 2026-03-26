"""Project CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectListOut
from services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectListOut])
async def list_projects(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all projects."""
    svc = ProjectService(db)
    projects = await svc.list_projects(skip=skip, limit=limit)
    return projects


@router.post("/", response_model=ProjectOut)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    svc = ProjectService(db)
    project = await svc.create_project(
        name=data.name,
        description=data.description,
        spec=data.spec,
        status=data.status,
    )
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a project by ID with its components."""
    svc = ProjectService(db)
    project = await svc.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    svc = ProjectService(db)
    update_data = data.model_dump(exclude_unset=True)
    project = await svc.update_project(project_id, **update_data)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a project."""
    svc = ProjectService(db)
    deleted = await svc.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"detail": "Project deleted"}
