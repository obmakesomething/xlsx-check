"""
프로젝트 비즈니스 로직 서비스.

프로젝트 CRUD, 상세 조회, 통계, 이력 관리 등 프로젝트 관련 핵심 로직을 담당한다.
"""

from __future__ import annotations
import logging
from typing import Any, Optional

from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import (
    Project, Component, CircuitBlock, DesignHistory, ChatMessage,
)
from rag.indexer import Indexer

logger = logging.getLogger(__name__)


class ProjectService:
    """CRUD operations for projects."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.indexer = Indexer()

    # ------------------------------------------------------------------
    # 목록 조회
    # ------------------------------------------------------------------

    async def list_projects(self, skip: int = 0, limit: int = 50,
                            status: Optional[str] = None) -> list[Project]:
        """프로젝트 목록을 조회한다. status 필터링 가능."""
        stmt = select(Project).order_by(Project.updated_at.desc())
        if status:
            stmt = stmt.where(Project.status == status)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # 단건 조회
    # ------------------------------------------------------------------

    async def get_project(self, project_id: int) -> Optional[Project]:
        """Get a project by ID with components loaded."""
        stmt = (
            select(Project)
            .options(selectinload(Project.components))
            .where(Project.id == project_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # 상세 조회 (부품, 회로 블록, 이력 모두 포함)
    # ------------------------------------------------------------------

    async def get_project_with_details(self, project_id: int) -> Optional[dict[str, Any]]:
        """
        프로젝트를 부품, 회로 블록, 설계 이력과 함께 조회한다.

        Returns
        -------
        dict | None  프로젝트가 존재하지 않으면 None
        """
        stmt = (
            select(Project)
            .options(
                selectinload(Project.components),
                selectinload(Project.circuit_blocks),
                selectinload(Project.design_history),
            )
            .where(Project.id == project_id)
        )
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if project is None:
            return None

        data = _project_to_dict(project)
        data["components"] = [
            {
                "id": c.id,
                "ref_designator": c.ref_designator,
                "part_number": c.part_number,
                "manufacturer": c.manufacturer,
                "description": c.description,
                "package": c.package,
                "quantity": c.quantity,
                "unit_price": c.unit_price,
                "lcsc_code": c.lcsc_code,
                "category": c.category,
                "properties": c.properties or {},
            }
            for c in project.components
        ]
        data["circuit_blocks"] = [
            {
                "id": b.id,
                "name": b.name,
                "block_type": b.block_type,
                "components": b.components or [],
                "description": b.description,
            }
            for b in project.circuit_blocks
        ]
        data["design_history"] = [
            {
                "id": h.id,
                "action": h.action,
                "details": h.details or {},
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in project.design_history
        ]
        return data

    # ------------------------------------------------------------------
    # 생성
    # ------------------------------------------------------------------

    async def create_project(self, name: str, description: str = "",
                              spec: dict[str, Any] | None = None,
                              status: str = "draft") -> Project:
        """새 프로젝트를 생성하고 설계 이력에 기록한다."""
        project = Project(
            name=name,
            description=description,
            spec=spec or {},
            status=status,
        )
        self.db.add(project)
        await self.db.flush()

        # 벡터 스토어에 인덱싱
        self.indexer.index_project(project.id, name, description, spec or {})

        # 설계 이력 기록
        history = DesignHistory(
            project_id=project.id,
            action="project_created",
            details={"name": name},
        )
        self.db.add(history)

        return project

    # ------------------------------------------------------------------
    # 업데이트
    # ------------------------------------------------------------------

    async def update_project(self, project_id: int, **kwargs) -> Optional[Project]:
        """프로젝트 필드를 업데이트하고 이력을 기록한다."""
        project = await self.get_project(project_id)
        if project is None:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)

        await self.db.flush()

        # 벡터 스토어 재인덱싱
        self.indexer.index_project(project.id, project.name, project.description, project.spec)

        # 이력 기록
        history = DesignHistory(
            project_id=project.id,
            action="project_updated",
            details={"updated_fields": list(kwargs.keys())},
        )
        self.db.add(history)

        return project

    # ------------------------------------------------------------------
    # 삭제 (캐스케이딩)
    # ------------------------------------------------------------------

    async def delete_project(self, project_id: int) -> bool:
        """프로젝트와 연관된 모든 데이터를 삭제한다 (ORM cascade)."""
        project = await self.get_project(project_id)
        if project is None:
            return False

        await self.db.delete(project)
        return True

    # ------------------------------------------------------------------
    # 통계
    # ------------------------------------------------------------------

    async def get_project_stats(self, project_id: int) -> Optional[dict[str, Any]]:
        """
        프로젝트의 통계 정보를 반환한다.

        - component_count: 부품 수
        - circuit_block_count: 회로 블록 수
        - history_count: 설계 이력 수
        - chat_message_count: 채팅 메시지 수
        - total_bom_cost: BOM 총 비용 추정치
        - last_activity: 마지막 활동 시각
        """
        # 프로젝트 존재 확인
        stmt = select(Project.id).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None

        # 부품 수 & BOM 비용
        comp_stmt = select(
            func.count(Component.id).label("count"),
            func.coalesce(
                func.sum(Component.unit_price * Component.quantity), 0.0
            ).label("total_cost"),
        ).where(Component.project_id == project_id)
        comp_row = (await self.db.execute(comp_stmt)).one()

        # 회로 블록 수
        block_stmt = select(func.count(CircuitBlock.id)).where(
            CircuitBlock.project_id == project_id
        )
        block_count = (await self.db.execute(block_stmt)).scalar() or 0

        # 설계 이력 수 & 마지막 활동
        hist_stmt = select(
            func.count(DesignHistory.id).label("count"),
            func.max(DesignHistory.created_at).label("last_at"),
        ).where(DesignHistory.project_id == project_id)
        hist_row = (await self.db.execute(hist_stmt)).one()

        # 채팅 메시지 수
        chat_stmt = select(func.count(ChatMessage.id)).where(
            ChatMessage.project_id == project_id
        )
        chat_count = (await self.db.execute(chat_stmt)).scalar() or 0

        last_activity = hist_row.last_at
        return {
            "project_id": project_id,
            "component_count": comp_row.count,
            "circuit_block_count": block_count,
            "history_count": hist_row.count,
            "chat_message_count": chat_count,
            "total_bom_cost": round(float(comp_row.total_cost), 2),
            "last_activity": last_activity.isoformat() if last_activity else None,
        }


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _project_to_dict(project: Project) -> dict[str, Any]:
    """Project ORM 객체를 dict 로 변환한다."""
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "spec": project.spec or {},
        "status": project.status,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }
