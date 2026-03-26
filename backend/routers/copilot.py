"""AI 코파일럿 채팅 및 분석 라우터."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional

from database.connection import get_db
from database.models import ChatMessage, Project
from database.schemas import ChatRequest, ChatMessageOut, CopilotAnalyzeRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_orchestrator():
    """오케스트레이터 인스턴스를 가져옵니다. 임포트 실패 시 None 반환."""
    try:
        from agents.orchestrator import Orchestrator
        return Orchestrator()
    except Exception as e:
        logger.warning(f"오케스트레이터 로드 실패: {e}")
        return None


@router.post("/chat")
async def chat(
    data: ChatRequest,
    task_type: Optional[str] = Query(None, description="작업 유형 (자동 감지 가능)"),
    db: AsyncSession = Depends(get_db),
):
    """코파일럿과 대화합니다."""
    # Verify project exists if project_id is provided
    if data.project_id is not None:
        proj_result = await db.execute(
            select(Project).where(Project.id == data.project_id)
        )
        if not proj_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    # Load recent chat history for context
    history: list[dict[str, str]] = []
    if data.project_id is not None:
        hist_stmt = (
            select(ChatMessage)
            .where(ChatMessage.project_id == data.project_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(20)
        )
        hist_result = await db.execute(hist_stmt)
        messages = list(reversed(hist_result.scalars().all()))
        history = [{"role": m.role, "content": m.content} for m in messages]

    # Save user message
    user_msg = ChatMessage(
        project_id=data.project_id,
        role="user",
        content=data.message,
        agent_type="user",
        metadata=data.context,
    )
    db.add(user_msg)
    await db.flush()

    # Get AI response
    orchestrator = _get_orchestrator()
    if orchestrator is None:
        ai_content = (
            "AI 에이전트를 초기화할 수 없습니다. "
            "ANTHROPIC_API_KEY가 설정되어 있는지 확인하세요."
        )
        agent_type = "orchestrator"
        response_meta = {"error": "orchestrator_unavailable"}
    else:
        context_str = ""
        if data.context:
            import json
            context_str = json.dumps(data.context, ensure_ascii=False)

        result = await orchestrator.route(
            user_message=data.message,
            context=context_str,
            task_type=task_type,
            history=history,
        )
        ai_content = result.get("content", "")
        agent_type = result.get("agent_type", "orchestrator")
        response_meta = {
            "task_type": result.get("task_type", "unknown"),
            "usage": result.get("usage", {}),
            "fallback": result.get("fallback", False),
        }

    # Save assistant message
    assistant_msg = ChatMessage(
        project_id=data.project_id,
        role="assistant",
        content=ai_content,
        agent_type=agent_type,
        metadata=response_meta,
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    return {
        "id": assistant_msg.id,
        "role": "assistant",
        "content": ai_content,
        "agent_type": agent_type,
        "metadata": response_meta,
        "created_at": assistant_msg.created_at,
    }


@router.post("/analyze")
async def analyze(
    data: CopilotAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """구조화된 분석을 수행합니다."""
    # Try to use copilot_service if available
    try:
        from services.copilot_service import CopilotService
        service = CopilotService()
        result = await service.analyze(
            user_request=data.user_request,
            project_spec=data.project_spec,
            file_bundle_summary=data.file_bundle_summary,
            bom_data=data.bom_data,
            previous_context=data.previous_context,
        )
    except ImportError:
        # Fallback to orchestrator directly
        orchestrator = _get_orchestrator()
        if orchestrator is None:
            raise HTTPException(
                status_code=503,
                detail="AI 서비스를 사용할 수 없습니다.",
            )

        import json
        context_parts = []
        if data.project_spec:
            context_parts.append(f"프로젝트 스펙: {json.dumps(data.project_spec, ensure_ascii=False)}")
        if data.file_bundle_summary:
            context_parts.append(f"파일 요약: {json.dumps(data.file_bundle_summary, ensure_ascii=False)}")
        if data.bom_data:
            context_parts.append(f"BOM 데이터: {json.dumps(data.bom_data[:50], ensure_ascii=False)}")

        context_str = "\n".join(context_parts)

        history = []
        if data.previous_context:
            history = [
                {"role": item.get("role", "user"), "content": item.get("content", "")}
                for item in data.previous_context
            ]

        result = await orchestrator.route(
            user_message=data.user_request,
            context=context_str,
            history=history,
        )

    # Save to chat history if project_id is provided
    if data.project_id is not None:
        user_msg = ChatMessage(
            project_id=data.project_id,
            role="user",
            content=data.user_request,
            agent_type="user",
            metadata={"type": "analyze"},
        )
        assistant_msg = ChatMessage(
            project_id=data.project_id,
            role="assistant",
            content=result.get("content", ""),
            agent_type=result.get("agent_type", "orchestrator"),
            metadata=result.get("structured", {}),
        )
        db.add(user_msg)
        db.add(assistant_msg)
        await db.flush()

    return result


@router.get("/history/{project_id}", response_model=list[ChatMessageOut])
async def get_chat_history(
    project_id: int,
    limit: int = Query(50, ge=1, le=500, description="조회할 메시지 수"),
    db: AsyncSession = Depends(get_db),
):
    """프로젝트의 채팅 기록을 조회합니다."""
    # Verify project exists
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.delete("/history/{project_id}", status_code=204)
async def clear_chat_history(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """프로젝트의 채팅 기록을 삭제합니다."""
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    await db.execute(
        delete(ChatMessage).where(ChatMessage.project_id == project_id)
    )
    await db.flush()
    return None
