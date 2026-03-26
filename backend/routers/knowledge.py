"""지식 베이스 관리 라우터."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from database.connection import get_db
from database.models import KnowledgeEntry
from database.schemas import KnowledgeEntryCreate, KnowledgeEntryUpdate, KnowledgeEntryOut

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[KnowledgeEntryOut])
async def list_knowledge_entries(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 항목 수"),
    offset: int = Query(0, ge=0, description="건너뛸 항목 수"),
    db: AsyncSession = Depends(get_db),
):
    """지식 베이스 항목 목록을 조회합니다."""
    stmt = select(KnowledgeEntry).order_by(KnowledgeEntry.created_at.desc())

    if category:
        stmt = stmt.where(KnowledgeEntry.category == category)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=KnowledgeEntryOut, status_code=201)
async def create_knowledge_entry(
    data: KnowledgeEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    """새 지식 항목을 추가합니다."""
    entry = KnowledgeEntry(
        category=data.category,
        title=data.title,
        content=data.content,
        source=data.source,
        tags=data.tags,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)

    # 벡터 스토어에도 추가 시도
    try:
        from rag.vector_store import VectorStore
        vs = VectorStore()
        vs.add_entry(
            entry_id=str(entry.id),
            text=f"{entry.title}\n{entry.content}",
            metadata={"category": entry.category, "source": entry.source},
        )
    except Exception as e:
        logger.warning("벡터 스토어 추가 실패 (비치명적): %s", e)

    return entry


@router.get("/search")
async def search_knowledge(
    q: str = Query(..., min_length=1, description="검색 쿼리"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    top_k: int = Query(10, ge=1, le=50, description="반환할 최대 결과 수"),
    db: AsyncSession = Depends(get_db),
):
    """지식 베이스를 검색합니다 (RAG 벡터 검색 + 키워드 폴백)."""
    # 1) 벡터 검색 시도
    vector_results = []
    try:
        from rag.vector_store import VectorStore
        vs = VectorStore()
        vector_results = vs.search(
            query=q,
            top_k=top_k,
            filter_metadata={"category": category} if category else None,
        )
    except Exception as e:
        logger.info("벡터 검색 불가, 키워드 검색으로 폴백: %s", e)

    if vector_results:
        # 벡터 검색 결과의 ID로 DB에서 전체 항목 조회
        entry_ids = []
        for vr in vector_results:
            try:
                entry_ids.append(int(vr.get("id", vr.get("entry_id", 0))))
            except (ValueError, TypeError):
                continue

        if entry_ids:
            stmt = select(KnowledgeEntry).where(KnowledgeEntry.id.in_(entry_ids))
            result = await db.execute(stmt)
            entries = result.scalars().all()

            # ID 순서 보존 (벡터 유사도 순서)
            entry_map = {e.id: e for e in entries}
            ordered = [entry_map[eid] for eid in entry_ids if eid in entry_map]

            return {
                "query": q,
                "method": "vector",
                "total": len(ordered),
                "results": [
                    KnowledgeEntryOut.model_validate(e).model_dump() for e in ordered
                ],
            }

    # 2) 키워드 폴백 검색
    pattern = f"%{q}%"
    stmt = select(KnowledgeEntry).where(
        or_(
            KnowledgeEntry.title.ilike(pattern),
            KnowledgeEntry.content.ilike(pattern),
        )
    )
    if category:
        stmt = stmt.where(KnowledgeEntry.category == category)

    stmt = stmt.order_by(KnowledgeEntry.created_at.desc()).limit(top_k)
    result = await db.execute(stmt)
    entries = result.scalars().all()

    return {
        "query": q,
        "method": "keyword",
        "total": len(entries),
        "results": [
            KnowledgeEntryOut.model_validate(e).model_dump() for e in entries
        ],
    }


@router.get("/{entry_id}", response_model=KnowledgeEntryOut)
async def get_knowledge_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 지식 항목을 조회합니다."""
    result = await db.execute(
        select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="지식 항목을 찾을 수 없습니다.")
    return entry


@router.put("/{entry_id}", response_model=KnowledgeEntryOut)
async def update_knowledge_entry(
    entry_id: int,
    data: KnowledgeEntryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """지식 항목을 수정합니다."""
    result = await db.execute(
        select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="지식 항목을 찾을 수 없습니다.")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(entry, key, value)

    await db.flush()
    await db.refresh(entry)

    # 벡터 스토어 업데이트 시도
    try:
        from rag.vector_store import VectorStore
        vs = VectorStore()
        vs.update_entry(
            entry_id=str(entry.id),
            text=f"{entry.title}\n{entry.content}",
            metadata={"category": entry.category, "source": entry.source},
        )
    except Exception as e:
        logger.warning("벡터 스토어 업데이트 실패 (비치명적): %s", e)

    return entry


@router.delete("/{entry_id}", status_code=204)
async def delete_knowledge_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """지식 항목을 삭제합니다."""
    result = await db.execute(
        select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="지식 항목을 찾을 수 없습니다.")

    # 벡터 스토어에서도 삭제 시도
    try:
        from rag.vector_store import VectorStore
        vs = VectorStore()
        vs.delete_entry(entry_id=str(entry.id))
    except Exception as e:
        logger.warning("벡터 스토어 삭제 실패 (비치명적): %s", e)

    await db.delete(entry)
    await db.flush()
    return None
