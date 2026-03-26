"""부품 관리 라우터."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from database.connection import get_db
from database.models import Component, Project
from database.schemas import ComponentCreate, ComponentUpdate, ComponentOut, SubstituteRequest

router = APIRouter()


@router.get("/", response_model=list[ComponentOut])
async def list_components(
    project_id: Optional[int] = Query(None, description="프로젝트 ID 필터"),
    query: Optional[str] = Query(None, description="검색어 (부품번호, 설명, 제조사)"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    manufacturer: Optional[str] = Query(None, description="제조사 필터"),
    db: AsyncSession = Depends(get_db),
):
    """부품 목록을 검색/조회합니다."""
    stmt = select(Component)

    if project_id is not None:
        stmt = stmt.where(Component.project_id == project_id)
    if category:
        stmt = stmt.where(Component.category == category)
    if manufacturer:
        stmt = stmt.where(Component.manufacturer.ilike(f"%{manufacturer}%"))
    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Component.part_number.ilike(pattern),
                Component.description.ilike(pattern),
                Component.manufacturer.ilike(pattern),
                Component.ref_designator.ilike(pattern),
            )
        )

    stmt = stmt.order_by(Component.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ComponentOut, status_code=201)
async def create_component(
    data: ComponentCreate,
    db: AsyncSession = Depends(get_db),
):
    """새 부품을 추가합니다."""
    # Verify project exists
    proj_result = await db.execute(
        select(Project).where(Project.id == data.project_id)
    )
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    component = Component(**data.model_dump())
    db.add(component)
    await db.flush()
    await db.refresh(component)
    return component


@router.get("/{component_id}", response_model=ComponentOut)
async def get_component(
    component_id: int,
    db: AsyncSession = Depends(get_db),
):
    """부품 상세 정보를 조회합니다."""
    result = await db.execute(
        select(Component).where(Component.id == component_id)
    )
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="부품을 찾을 수 없습니다.")
    return component


@router.put("/{component_id}", response_model=ComponentOut)
async def update_component(
    component_id: int,
    data: ComponentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """부품 정보를 수정합니다."""
    result = await db.execute(
        select(Component).where(Component.id == component_id)
    )
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="부품을 찾을 수 없습니다.")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(component, key, value)

    await db.flush()
    await db.refresh(component)
    return component


@router.delete("/{component_id}", status_code=204)
async def delete_component(
    component_id: int,
    db: AsyncSession = Depends(get_db),
):
    """부품을 삭제합니다."""
    result = await db.execute(
        select(Component).where(Component.id == component_id)
    )
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="부품을 찾을 수 없습니다.")

    await db.delete(component)
    await db.flush()
    return None


@router.post("/search-lcsc")
async def search_lcsc(
    keyword: str = Query(..., description="LCSC 검색 키워드"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
):
    """LCSC에서 부품을 검색합니다."""
    try:
        from services.lcsc_service import LCSCService
        service = LCSCService()
        results = await service.search(keyword=keyword, category=category)
        return {"results": results, "keyword": keyword}
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="LCSC 서비스 모듈이 아직 구현되지 않았습니다.",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LCSC 검색 실패: {str(e)}")


@router.post("/substitute")
async def find_substitute(
    data: SubstituteRequest,
    db: AsyncSession = Depends(get_db),
):
    """주어진 부품의 대체 부품을 검색합니다."""
    # Load the original component
    result = await db.execute(
        select(Component).where(Component.id == data.component_id)
    )
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="부품을 찾을 수 없습니다.")

    try:
        from services.lcsc_service import LCSCService
        service = LCSCService()
        substitutes = await service.find_substitutes(
            part_number=component.part_number,
            category=component.category,
            package=component.package,
            reason=data.reason,
        )
        return {
            "original": ComponentOut.model_validate(component).model_dump(),
            "substitutes": substitutes,
            "reason": data.reason,
        }
    except ImportError:
        # Fallback: return a helpful message when service is not yet implemented
        return {
            "original": ComponentOut.model_validate(component).model_dump(),
            "substitutes": [],
            "reason": data.reason,
            "message": "LCSC 서비스가 아직 구현되지 않았습니다. 수동으로 대체 부품을 검색하세요.",
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"대체 부품 검색 실패: {str(e)}")
