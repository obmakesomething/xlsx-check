"""AI copilot chat and analysis endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
import asyncio

from database.connection import get_db
from database.schemas import ChatRequest, CopilotAnalyzeRequest, ChatMessageOut
from services.copilot_service import CopilotService

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.post("/chat")
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Main chat endpoint. Returns AI copilot response.

    Supports streaming via Accept: text/event-stream header (SSE),
    otherwise returns JSON.
    """
    svc = CopilotService(db)
    result = await svc.chat(
        message=data.message,
        project_id=data.project_id,
        context=data.context,
    )
    return result


@router.post("/chat/stream")
async def chat_stream(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Streaming chat endpoint using Server-Sent Events."""
    svc = CopilotService(db)

    async def event_generator():
        # Send initial event
        yield f"data: {json.dumps({'type': 'start', 'agent_type': 'orchestrator'})}\n\n"

        # Get the response (for now, we get the full response and stream it in chunks)
        result = await svc.chat(
            message=data.message,
            project_id=data.project_id,
            context=data.context,
        )

        content = result.get("message", "")
        # Stream content in chunks
        chunk_size = 50
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield f"data: {json.dumps({'type': 'content', 'text': chunk})}\n\n"
            await asyncio.sleep(0.02)

        # Send metadata
        yield f"data: {json.dumps({'type': 'metadata', 'agent_type': result.get('agent_type', ''), 'task_type': result.get('task_type', '')})}\n\n"

        # End event
        yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/analyze")
async def analyze(
    data: CopilotAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Structured analysis endpoint returning full JSON schema response."""
    svc = CopilotService(db)
    result = await svc.analyze(
        user_request=data.user_request,
        project_spec=data.project_spec,
        file_bundle_summary=data.file_bundle_summary,
        bom_data=data.bom_data,
        previous_context=data.previous_context,
        project_id=data.project_id,
    )
    return result


@router.get("/history/{project_id}", response_model=list[ChatMessageOut])
async def get_chat_history(
    project_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a project."""
    svc = CopilotService(db)
    messages = await svc.get_chat_history(project_id, limit=limit)
    return messages
