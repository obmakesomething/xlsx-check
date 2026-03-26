"""
부품(Component) 관리 서비스.

부품 CRUD, 검색, 대체품 탐색, 사용 이력 조회 등을 처리한다.
"""

from __future__ import annotations
import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Component, Project, DesignHistory
from rag.indexer import Indexer
from rag.retriever import Retriever

logger = logging.getLogger(__name__)


class ComponentService:
    """CRUD and search operations for components."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.indexer = Indexer()
        self.retriever = Retriever()

    async def list_components(
        self,
        project_id: Optional[int] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Component]:
        """List components with optional filters."""
        stmt = select(Component)
        if project_id is not None:
            stmt = stmt.where(Component.project_id == project_id)
        if category:
            stmt = stmt.where(Component.category == category)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                Component.part_number.ilike(pattern)
                | Component.description.ilike(pattern)
                | Component.manufacturer.ilike(pattern)
                | Component.ref_designator.ilike(pattern)
            )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_component(self, component_id: int) -> Optional[Component]:
        """Get a component by ID."""
        stmt = select(Component).where(Component.id == component_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_component(self, **kwargs) -> Component:
        """Create a new component."""
        comp = Component(**kwargs)
        self.db.add(comp)
        await self.db.flush()

        # Index
        self.indexer.index_components(comp.project_id, [kwargs])

        return comp

    async def update_component(self, component_id: int, **kwargs) -> Optional[Component]:
        """Update a component."""
        comp = await self.get_component(component_id)
        if comp is None:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(comp, key):
                setattr(comp, key, value)

        await self.db.flush()
        return comp

    async def delete_component(self, component_id: int) -> bool:
        """Delete a component."""
        comp = await self.get_component(component_id)
        if comp is None:
            return False
        await self.db.delete(comp)
        return True

    async def bulk_create(self, project_id: int, components: list[dict[str, Any]]) -> list[Component]:
        """Bulk create components for a project."""
        created = []
        for data in components:
            data["project_id"] = project_id
            comp = Component(**data)
            self.db.add(comp)
            created.append(comp)

        await self.db.flush()

        # Index all at once
        self.indexer.index_components(project_id, components)

        # Record history
        history = DesignHistory(
            project_id=project_id,
            action="components_imported",
            details={"count": len(components)},
        )
        self.db.add(history)

        return created

    async def find_substitutes(self, component_id: int, reason: str = "cost_reduction") -> list[dict[str, Any]]:
        """Find substitute parts using RAG similarity search."""
        comp = await self.get_component(component_id)
        if comp is None:
            return []

        query = f"{comp.description} {comp.package} {comp.category}"
        results = self.retriever.retrieve_components(query, n=10)

        substitutes = []
        for r in results:
            meta = r.get("metadata", {})
            if meta.get("part_number") and meta.get("part_number") != comp.part_number:
                substitutes.append({
                    "part_number": meta.get("part_number", ""),
                    "category": meta.get("category", ""),
                    "relevance_score": 1.0 - (r.get("distance", 1.0) or 1.0),
                    "source": "rag_similarity",
                    "document": r.get("document", ""),
                })

        return substitutes

    async def get_component_usage_history(self, part_number: str) -> dict[str, Any]:
        """
        특정 part_number 가 사용된 모든 프로젝트와 사용 내역을 반환한다.

        Returns
        -------
        dict  { part_number, usage: [...], total_projects, total_quantity }
        """
        if not part_number:
            return {"part_number": part_number, "usage": [], "total_projects": 0, "total_quantity": 0}

        stmt = (
            select(
                Component.id,
                Component.project_id,
                Component.ref_designator,
                Component.quantity,
                Component.description,
                Project.name.label("project_name"),
                Project.status.label("project_status"),
            )
            .join(Project, Component.project_id == Project.id)
            .where(Component.part_number == part_number)
            .order_by(Project.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        usage_list: list[dict[str, Any]] = []
        project_ids: set[int] = set()
        for row in rows:
            project_ids.add(row.project_id)
            usage_list.append({
                "component_id": row.id,
                "project_id": row.project_id,
                "project_name": row.project_name,
                "project_status": row.project_status,
                "ref_designator": row.ref_designator,
                "quantity": row.quantity,
                "description": row.description,
            })

        return {
            "part_number": part_number,
            "usage": usage_list,
            "total_projects": len(project_ids),
            "total_quantity": sum(u["quantity"] for u in usage_list),
        }
