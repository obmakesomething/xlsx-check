"""
지식 베이스 관리 서비스.

RAG 기반 지식 검색, 지식 항목 CRUD, 초기 시딩(backend/data/*.json),
인터뷰 트랜스크립트에서 설계 원칙 추출 등을 처리한다.
"""

from __future__ import annotations
import json
import logging
import pathlib
import re
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import KnowledgeEntry
from rag.indexer import Indexer
from rag.retriever import Retriever

logger = logging.getLogger(__name__)

# backend/data/ 디렉토리 경로
_DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


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

    # ------------------------------------------------------------------
    # 초기 시딩 (backend/data/*.json 파일 기반)
    # ------------------------------------------------------------------

    async def seed_initial_knowledge(self) -> dict[str, Any]:
        """
        backend/data/ 디렉토리의 JSON 파일들을 읽어 지식 베이스를 시딩한다.

        지원 파일 형식 (design_principles.json 등):
        { "principles": [ { "id", "category", "title", "content", "priority", "tags" } ] }

        Returns
        -------
        dict  { seeded_count, skipped_count, files_processed }
        """
        seeded = 0
        skipped = 0
        files_processed: list[str] = []

        if not _DATA_DIR.exists():
            logger.warning("데이터 디렉토리 없음: %s", _DATA_DIR)
            return {"seeded_count": 0, "skipped_count": 0, "files_processed": []}

        for json_file in sorted(_DATA_DIR.glob("*.json")):
            try:
                raw = json.loads(json_file.read_text(encoding="utf-8"))
                files_processed.append(json_file.name)

                # design_principles.json 형식 처리
                principles = raw.get("principles", [])
                for p in principles:
                    # 중복 확인 (같은 title 이 이미 있으면 skip)
                    dup_stmt = select(KnowledgeEntry.id).where(
                        KnowledgeEntry.title == p.get("title", "")
                    )
                    dup_result = await self.db.execute(dup_stmt)
                    if dup_result.scalar_one_or_none() is not None:
                        skipped += 1
                        continue

                    try:
                        await self.create_entry(
                            category=p.get("category", "GENERAL"),
                            title=p.get("title", ""),
                            content=p.get("content", ""),
                            source=f"seed:{json_file.name}",
                            tags=p.get("tags", []),
                        )
                        seeded += 1
                    except Exception as exc:
                        logger.warning("시딩 실패: %s - %s", p.get("title"), exc)
                        skipped += 1

            except Exception as exc:
                logger.error("파일 처리 실패: %s - %s", json_file.name, exc)

        logger.info(
            "지식 베이스 시딩 완료: seeded=%d, skipped=%d, files=%s",
            seeded, skipped, files_processed,
        )
        return {
            "seeded_count": seeded,
            "skipped_count": skipped,
            "files_processed": files_processed,
        }

    # ------------------------------------------------------------------
    # 인터뷰 트랜스크립트 처리
    # ------------------------------------------------------------------

    async def process_interview_transcript(
        self,
        text: str,
        source: str = "interview",
    ) -> dict[str, Any]:
        """
        인터뷰 텍스트에서 설계 원칙/노하우를 추출하여 지식 베이스에 추가한다.

        단락을 분리하고 각 단락에서 카테고리를 추정하여 항목으로 등록한다.
        (간이 추출 로직 - 운영 환경에서는 LLM 기반 추출 권장)

        Parameters
        ----------
        text : str
            인터뷰 트랜스크립트 전문
        source : str
            출처 라벨

        Returns
        -------
        dict  { extracted_count, entries: [...] }
        """
        if not text or not text.strip():
            return {"extracted_count": 0, "entries": []}

        # 단락 분리: 빈 줄 또는 번호 패턴 기준
        paragraphs = re.split(r"\n\s*\n|\n(?=\d+[\.\)]\s)", text.strip())
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 30]

        # 카테고리 추정 키워드 맵
        category_hints: dict[str, list[str]] = {
            "IC_SELECTION": ["IC", "드라이버", "레귤레이터", "컨버터", "토폴로지"],
            "PROTECTION": ["보호", "서지", "ESD", "TVS", "MOV", "퓨즈"],
            "RF_DESIGN": ["RF", "안테나", "블루투스", "WiFi", "BLE", "무선"],
            "CERTIFICATION": ["인증", "KC", "CE", "UL", "EMC", "안전"],
            "PRODUCTION": ["양산", "SMT", "PCB", "공정", "BOM", "원가", "테스트"],
            "THERMAL": ["방열", "열", "온도", "히트싱크", "열저항"],
        }

        entries: list[dict[str, Any]] = []

        for para in paragraphs:
            # 카테고리 추정
            category = "GENERAL"
            max_score = 0
            for cat, keywords in category_hints.items():
                score = sum(1 for kw in keywords if kw in para)
                if score > max_score:
                    max_score = score
                    category = cat

            # 제목: 첫 문장 (최대 80자)
            first_sentence = para.split(".")[0].split("。")[0][:80].strip()
            if not first_sentence:
                continue

            # 태그 추출: 영문 대문자 약어
            tags = list(set(re.findall(r"[A-Z]{2,}[0-9]*", para)))[:5]

            try:
                entry = await self.create_entry(
                    category=category,
                    title=first_sentence,
                    content=para,
                    source=source,
                    tags=tags,
                )
                entries.append({
                    "id": entry.id,
                    "category": entry.category,
                    "title": entry.title,
                })
            except Exception as exc:
                logger.warning("인터뷰 항목 추가 실패: %s - %s", first_sentence[:30], exc)

        logger.info("인터뷰 트랜스크립트 처리 완료: %d개 항목 추출", len(entries))
        return {
            "extracted_count": len(entries),
            "entries": entries,
        }


# ---------------------------------------------------------------------------
# 모듈 수준 편의 함수
# ---------------------------------------------------------------------------

def search_knowledge(
    query: str,
    category: Optional[str] = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """DB 세션 없이 RAG 검색만 수행하는 편의 함수."""
    retriever = Retriever()
    return retriever.search_knowledge(query, n_results=top_k, category=category)


async def add_knowledge_entry(db: AsyncSession, data: dict[str, Any]) -> KnowledgeEntry:
    """지식 항목 추가 편의 함수."""
    svc = KnowledgeService(db)
    return await svc.create_entry(
        category=data.get("category", "GENERAL"),
        title=data.get("title", ""),
        content=data.get("content", ""),
        source=data.get("source", ""),
        tags=data.get("tags", []),
    )


async def seed_initial_knowledge(db: AsyncSession) -> dict[str, Any]:
    """초기 시딩 편의 함수."""
    svc = KnowledgeService(db)
    return await svc.seed_initial_knowledge()


async def process_interview_transcript(
    db: AsyncSession,
    text: str,
    source: str = "interview",
) -> dict[str, Any]:
    """인터뷰 트랜스크립트 처리 편의 함수."""
    svc = KnowledgeService(db)
    return await svc.process_interview_transcript(text, source=source)
