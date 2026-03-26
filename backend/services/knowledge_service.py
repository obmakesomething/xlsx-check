"""Knowledge base management service."""

from __future__ import annotations
import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import KnowledgeEntry
from rag.indexer import Indexer
from rag.retriever import Retriever

logger = logging.getLogger(__name__)


class KnowledgeService:
    """CRUD and search for the knowledge base."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.indexer = Indexer()
        self.retriever = Retriever()

    async def list_entries(
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[KnowledgeEntry]:
        """List knowledge entries with optional category filter."""
        stmt = select(KnowledgeEntry).order_by(KnowledgeEntry.created_at.desc())
        if category:
            stmt = stmt.where(KnowledgeEntry.category == category)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_entry(self, entry_id: int) -> Optional[KnowledgeEntry]:
        """Get a knowledge entry by ID."""
        stmt = select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_entry(
        self,
        category: str,
        title: str,
        content: str,
        source: str = "",
        tags: list[str] | None = None,
    ) -> KnowledgeEntry:
        """Create a new knowledge entry and index it."""
        entry = KnowledgeEntry(
            category=category,
            title=title,
            content=content,
            source=source,
            tags=tags or [],
        )
        self.db.add(entry)
        await self.db.flush()

        # Index in vector store
        self.indexer.index_knowledge(entry.id, category, title, content, tags or [])

        return entry

    async def update_entry(self, entry_id: int, **kwargs) -> Optional[KnowledgeEntry]:
        """Update a knowledge entry."""
        entry = await self.get_entry(entry_id)
        if entry is None:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(entry, key):
                setattr(entry, key, value)

        await self.db.flush()

        # Re-index
        self.indexer.index_knowledge(
            entry.id, entry.category, entry.title, entry.content, entry.tags or []
        )

        return entry

    async def delete_entry(self, entry_id: int) -> bool:
        """Delete a knowledge entry."""
        entry = await self.get_entry(entry_id)
        if entry is None:
            return False
        await self.db.delete(entry)
        return True

    def search(self, query: str, category: Optional[str] = None, n_results: int = 10) -> list[dict[str, Any]]:
        """Search knowledge base using vector similarity."""
        return self.retriever.search_knowledge(query, n_results=n_results, category=category)

    async def get_categories(self) -> list[str]:
        """Get all unique categories."""
        from sqlalchemy import distinct
        stmt = select(distinct(KnowledgeEntry.category))
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]
