"""Main copilot service implementing the full JSON schema task router."""

from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import ChatMessage, DesignHistory
from agents.orchestrator import Orchestrator
from rag.retriever import Retriever

logger = logging.getLogger(__name__)

# All recognized task types
TASK_TYPES = [
    "import_metadata",
    "search_summarize",
    "design_draft",
    "bom_normalize",
    "substitute_parts",
    "china_sourcing",
    "review",
    "checklist",
    "compare",
    "report",
    "mixed",
    "unknown",
]


class CopilotService:
    """Core copilot logic: analyze user requests and return structured JSON responses."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.orchestrator = Orchestrator()
        self.retriever = Retriever()

    async def chat(
        self,
        message: str,
        project_id: Optional[int] = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle a chat message and return a response."""
        # Save user message
        user_msg = ChatMessage(
            project_id=project_id,
            role="user",
            content=message,
            agent_type="user",
            metadata=context or {},
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Get RAG context
        rag_context = self.retriever.get_context_for_query(message)

        # Get chat history
        history = await self._get_history(project_id, limit=10)

        # Route through orchestrator
        result = await self.orchestrator.route(
            user_message=message,
            context=rag_context,
            history=history,
        )

        # Save assistant message
        assistant_msg = ChatMessage(
            project_id=project_id,
            role="assistant",
            content=result.get("content", ""),
            agent_type=result.get("agent_type", "orchestrator"),
            metadata={
                "task_type": result.get("task_type", "unknown"),
                "usage": result.get("usage", {}),
            },
        )
        self.db.add(assistant_msg)

        return {
            "message": result.get("content", ""),
            "agent_type": result.get("agent_type", "orchestrator"),
            "task_type": result.get("task_type", "unknown"),
            "metadata": result.get("usage", {}),
        }

    async def analyze(
        self,
        user_request: str,
        project_spec: dict[str, Any] | None = None,
        file_bundle_summary: dict[str, Any] | None = None,
        bom_data: list[dict[str, Any]] | None = None,
        previous_context: list[dict[str, Any]] | None = None,
        project_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Execute structured analysis and return the full JSON schema response."""

        # Step 1: Determine task type
        task_type = self.orchestrator.detect_task_type(user_request)

        # Step 2: Get RAG context
        rag_context = self.retriever.get_context_for_query(user_request)

        # Step 3: Build comprehensive context
        full_context = self._build_context(
            user_request=user_request,
            project_spec=project_spec,
            file_bundle_summary=file_bundle_summary,
            bom_data=bom_data,
            previous_context=previous_context,
            rag_context=rag_context,
        )

        # Step 4: Route to appropriate agent(s) with structured output
        agent_result = await self.orchestrator.route(
            user_message=user_request,
            context=full_context,
            task_type=task_type,
        )

        # Step 5: Build the full JSON response
        response = self._build_response(
            task_type=task_type,
            user_request=user_request,
            agent_result=agent_result,
            project_spec=project_spec or {},
            file_bundle_summary=file_bundle_summary or {},
            bom_data=bom_data or [],
        )

        # Step 6: Record in DB
        if project_id:
            history = DesignHistory(
                project_id=project_id,
                action=f"copilot_analyze_{task_type}",
                details={"user_request": user_request, "task_type": task_type},
            )
            self.db.add(history)

        return response

    async def get_chat_history(self, project_id: int, limit: int = 50) -> list[dict[str, Any]]:
        """Get chat message history for a project."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.project_id == project_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "agent_type": msg.agent_type,
                "metadata": msg.metadata,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ]

    async def _get_history(self, project_id: Optional[int], limit: int = 10) -> list[dict[str, str]]:
        """Get recent chat history formatted for LLM context."""
        if project_id is None:
            return []

        stmt = (
            select(ChatMessage)
            .where(ChatMessage.project_id == project_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()

        history = []
        for msg in messages:
            if msg.role in ("user", "assistant"):
                history.append({"role": msg.role, "content": msg.content})
        return history

    def _build_context(
        self,
        user_request: str,
        project_spec: dict | None,
        file_bundle_summary: dict | None,
        bom_data: list | None,
        previous_context: list | None,
        rag_context: str,
    ) -> str:
        """Build a comprehensive context string for the agent."""
        parts = []

        if project_spec:
            parts.append(f"[프로젝트 사양]\n{json.dumps(project_spec, ensure_ascii=False, indent=2)}")

        if file_bundle_summary:
            parts.append(f"[파일 번들 요약]\n{json.dumps(file_bundle_summary, ensure_ascii=False, indent=2)}")

        if bom_data:
            bom_preview = bom_data[:20]
            parts.append(f"[BOM 데이터 (처음 {len(bom_preview)}개)]\n{json.dumps(bom_preview, ensure_ascii=False, indent=2)}")

        if previous_context:
            ctx_strs = []
            for ctx in previous_context[-5:]:
                ctx_strs.append(f"- {ctx.get('role', 'user')}: {str(ctx.get('content', ''))[:200]}")
            parts.append(f"[이전 대화 맥락]\n" + "\n".join(ctx_strs))

        if rag_context:
            parts.append(f"[RAG 참고 자료]\n{rag_context}")

        return "\n\n".join(parts)

    def _build_response(
        self,
        task_type: str,
        user_request: str,
        agent_result: dict[str, Any],
        project_spec: dict,
        file_bundle_summary: dict,
        bom_data: list,
    ) -> dict[str, Any]:
        """Build the full copilot JSON response schema."""
        now = datetime.now(timezone.utc).isoformat()
        agent_content = agent_result.get("content", "")

        response = {
            "meta": {
                "task_type": task_type,
                "timestamp": now,
                "agent_type": agent_result.get("agent_type", "orchestrator"),
                "model_usage": agent_result.get("usage", {}),
            },
            "input_summary": {
                "user_request": user_request,
                "has_project_spec": bool(project_spec),
                "has_file_bundle": bool(file_bundle_summary),
                "bom_row_count": len(bom_data),
            },
            "analysis": {
                "summary": agent_content[:500] if agent_content else "분석 결과가 없습니다.",
                "full_response": agent_content,
                "structured_data": agent_result.get("structured", None),
            },
            "recommendations": self._extract_recommendations(task_type, agent_content),
            "action_items": self._extract_action_items(task_type, agent_content, bom_data),
            "warnings": [],
            "next_steps": self._suggest_next_steps(task_type),
        }

        # Task-specific sections
        if task_type == "design_draft":
            response["design"] = {
                "topology": "",
                "circuit_blocks": [],
                "key_components": [],
                "calculations": {},
            }
        elif task_type == "bom_normalize":
            response["bom"] = {
                "normalized_count": len(bom_data),
                "issues_found": [],
                "suggestions": [],
            }
        elif task_type == "substitute_parts":
            response["substitutes"] = {
                "original_parts": [],
                "alternatives": [],
                "cost_comparison": {},
            }
        elif task_type == "china_sourcing":
            response["sourcing"] = {
                "lcsc_results": [],
                "price_summary": {},
                "availability_notes": [],
            }
        elif task_type == "checklist":
            response["checklist"] = {
                "items": [],
                "completed": 0,
                "total": 0,
                "category": "",
            }
        elif task_type == "review":
            response["review"] = {
                "score": 0,
                "issues": [],
                "passed": [],
                "critical_findings": [],
            }
        elif task_type == "compare":
            response["comparison"] = {
                "items": [],
                "differences": [],
                "recommendation": "",
            }
        elif task_type == "report":
            response["report"] = {
                "title": "",
                "sections": [],
                "format": "markdown",
            }
        elif task_type == "import_metadata":
            response["import"] = {
                "file_type": file_bundle_summary.get("format", "unknown"),
                "components_found": 0,
                "nets_found": 0,
                "metadata": file_bundle_summary,
            }

        return response

    def _extract_recommendations(self, task_type: str, content: str) -> list[dict[str, str]]:
        """Extract recommendations from agent response."""
        recs = []
        if not content:
            return recs

        # Simple heuristic: look for numbered or bulleted items
        import re
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if re.match(r"^[\d]+[\.\)]\s+", line) or line.startswith("- ") or line.startswith("* "):
                clean = re.sub(r"^[\d]+[\.\)]\s+|^[-*]\s+", "", line)
                if len(clean) > 10:
                    priority = "high" if any(w in clean for w in ["중요", "필수", "반드시", "critical", "must"]) else "medium"
                    recs.append({"text": clean, "priority": priority})

        return recs[:10]

    def _extract_action_items(self, task_type: str, content: str, bom_data: list) -> list[dict[str, str]]:
        """Generate action items based on task type."""
        items = []

        if task_type == "design_draft":
            items.append({"action": "회로도 작성", "status": "pending", "detail": "제안된 토폴로지 기반 회로도 작성"})
            items.append({"action": "시뮬레이션 실행", "status": "pending", "detail": "핵심 회로 블록 시뮬레이션"})
        elif task_type == "bom_normalize":
            items.append({"action": "BOM 검증", "status": "pending", "detail": f"{len(bom_data)}개 부품 정규화 검증"})
            items.append({"action": "누락 부품 확인", "status": "pending", "detail": "필수 부품 누락 여부 확인"})
        elif task_type == "review":
            items.append({"action": "지적사항 수정", "status": "pending", "detail": "리뷰 결과 반영"})
        elif task_type == "checklist":
            items.append({"action": "체크리스트 완료", "status": "pending", "detail": "모든 항목 확인"})
        elif task_type == "substitute_parts":
            items.append({"action": "대체 부품 검증", "status": "pending", "detail": "전기적 호환성 확인"})
            items.append({"action": "가격 비교", "status": "pending", "detail": "대체 부품 가격 비교표 작성"})

        return items

    def _suggest_next_steps(self, task_type: str) -> list[str]:
        """Suggest next steps based on the current task type."""
        suggestions = {
            "design_draft": [
                "회로 시뮬레이션을 실행하여 동작 확인",
                "BOM 작성 및 부품 소싱",
                "PCB 레이아웃 설계 진행",
            ],
            "bom_normalize": [
                "LCSC에서 부품 가격 조회",
                "대체 부품 검토",
                "회로도와 BOM 일치 여부 확인",
            ],
            "substitute_parts": [
                "대체 부품 데이터시트 비교 검토",
                "프로토타입에서 호환성 테스트",
                "가격 협상 진행",
            ],
            "china_sourcing": [
                "샘플 주문 진행",
                "납기 일정 확인",
                "MOQ 및 결제 조건 협의",
            ],
            "review": [
                "지적사항 수정 후 재검토 요청",
                "수정 이력 문서화",
                "최종 승인 프로세스 진행",
            ],
            "checklist": [
                "미완료 항목 처리",
                "인증 시험소 연락",
                "관련 문서 준비",
            ],
            "compare": [
                "비교 결과 기반 최종 선택",
                "선택된 방안으로 상세 설계 진행",
            ],
            "report": [
                "리포트 검토 및 수정",
                "관련자 배포",
            ],
            "import_metadata": [
                "파싱된 데이터 검증",
                "BOM과 회로도 교차 확인",
                "누락 정보 보완",
            ],
        }
        return suggestions.get(task_type, ["추가 질문이 있으시면 말씀해 주세요."])
