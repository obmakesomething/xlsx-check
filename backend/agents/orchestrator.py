"""Orchestrator agent - routes queries to specialized agents."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

ORCHESTRATOR_PROMPT = """당신은 조명/센서/RF 전자제품 개발 전문가의 AI 코파일럿 오케스트레이터입니다.

사용자의 요청을 분석하여 적절한 전문 에이전트로 라우팅합니다.

## 에이전트 목록
1. CIRCUIT: 회로 설계 (스키매틱, BoM, IC 선정, 보호회로, 토폴로지)
2. RF: RF/무선 통신 (2.4GHz, BLE, WiFi, Matter, Zigbee, 안테나)
3. MECHANICAL: 기구 검토 (PCB 사이즈, 방열, 하우징, 3D 적합성)
4. CERTIFICATION: 인증/양산 (KC, 안전, EMC, 에너지효율, 원가)
5. GENERAL: 일반 질문, 업계 정보, 설계 원칙

## task_type 판별
사용자 요청을 분석하여 다음 중 하나로 분류:
- import_metadata: 파일/문서에서 메타데이터 추출
- search_summarize: 기존 회로/레퍼런스 검색 및 요약
- design_draft: 요구사항을 회로 구조안으로 변환
- bom_normalize: BOM 정리 및 정규화
- substitute_parts: 대체부품 추천
- china_sourcing: 중국 조달/LCSC/JLC 중심 추천
- review: 회로/BOM/요구사항 리스크 분석
- checklist: 테스트 체크리스트 생성
- compare: 두 회로/BOM 비교
- report: 종합 리포트 생성
- mixed: 여러 작업이 섞임
- unknown: 판단 불가

## 응답 형식 (반드시 JSON)
{
  "agent": "CIRCUIT|RF|MECHANICAL|CERTIFICATION|GENERAL",
  "task_type": "위 task_type 중 하나",
  "refined_query": "에이전트에게 전달할 정제된 쿼리",
  "context_needed": ["past_projects", "bom_history", "certification_data", "knowledge_base"],
  "multi_agent": false,
  "agents_needed": ["필요한 에이전트들"]
}
"""


class OrchestratorAgent(BaseAgent):
    """Routes queries to the appropriate specialized agent."""

    agent_type = "orchestrator"
    system_prompt = ORCHESTRATOR_PROMPT

    def __init__(self):
        super().__init__()
        self._agents: dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        """Register a specialized agent."""
        self._agents[agent.agent_type.upper()] = agent

    def get_registered_agents(self) -> list[str]:
        return list(self._agents.keys())

    async def route(self, user_message: str, context: str = "") -> dict[str, Any]:
        """Analyze user message and determine routing."""
        result = await self.run_structured(user_message, context=context)
        routing = result.get("structured")

        if routing is None:
            routing = self._rule_based_routing(user_message)

        return routing

    async def execute(
        self,
        user_message: str,
        context: str = "",
        task_type: Optional[str] = None,
        history: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """Route and execute query through the appropriate agent(s)."""

        # Step 1: Route
        if task_type:
            routing = self._route_by_task_type(task_type, user_message)
        else:
            routing = await self.route(user_message, context)

        agent_name = routing.get("agent", "GENERAL").upper()
        detected_task_type = routing.get("task_type", "unknown")
        refined_query = routing.get("refined_query", user_message)
        multi_agent = routing.get("multi_agent", False)

        # Step 2: Execute
        if multi_agent and routing.get("agents_needed"):
            results = await self._execute_multi_agent(
                routing["agents_needed"], refined_query, context, history
            )
            return {
                "routing": routing,
                "task_type": detected_task_type,
                "results": results,
                "agent_type": "multi",
            }
        else:
            agent = self._agents.get(agent_name)
            if agent is None:
                agent = self._agents.get("GENERAL") or self._agents.get("CIRCUIT")

            if agent:
                result = await agent.run(refined_query, context=context, history=history)
            else:
                result = await self.run(refined_query, context=context, history=history)

            result["routing"] = routing
            result["task_type"] = detected_task_type
            return result

    async def _execute_multi_agent(
        self,
        agent_names: list[str],
        query: str,
        context: str,
        history: Optional[list[dict]],
    ) -> list[dict[str, Any]]:
        """Execute query across multiple agents."""
        import asyncio

        tasks = []
        for name in agent_names:
            agent = self._agents.get(name.upper())
            if agent:
                tasks.append(agent.run(query, context=context, history=history))

        if not tasks:
            return [await self.run(query, context=context, history=history)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = []
        for r in results:
            if isinstance(r, Exception):
                output.append({"error": str(r)})
            else:
                output.append(r)
        return output

    def _rule_based_routing(self, message: str) -> dict[str, Any]:
        """Fallback rule-based routing when LLM routing fails."""
        msg = message.lower()

        circuit_kw = ["회로", "스키매틱", "드라이버", "ic", "보호회로", "토폴로지", "bom", "부품", "led"]
        rf_kw = ["rf", "무선", "2.4ghz", "ble", "bluetooth", "wifi", "zigbee", "matter", "안테나", "통신", "리모컨"]
        mech_kw = ["기구", "하우징", "pcb 사이즈", "방열", "3d", "금형", "케이스"]
        cert_kw = ["인증", "kc", "emc", "전자파", "안전", "양산", "원가", "jlcpcb", "제조"]

        agent = "GENERAL"
        if any(kw in msg for kw in rf_kw):
            agent = "RF"
        elif any(kw in msg for kw in cert_kw):
            agent = "CERTIFICATION"
        elif any(kw in msg for kw in mech_kw):
            agent = "MECHANICAL"
        elif any(kw in msg for kw in circuit_kw):
            agent = "CIRCUIT"

        task_type = "unknown"
        if any(kw in msg for kw in ["메타데이터", "추출", "파일 분석"]):
            task_type = "import_metadata"
        elif any(kw in msg for kw in ["검색", "찾아", "유사한", "레퍼런스"]):
            task_type = "search_summarize"
        elif any(kw in msg for kw in ["설계", "만들어", "구조안", "드래프트"]):
            task_type = "design_draft"
        elif any(kw in msg for kw in ["bom 정리", "정규화", "bom 분석"]):
            task_type = "bom_normalize"
        elif any(kw in msg for kw in ["대체", "substitute", "대안", "호환"]):
            task_type = "substitute_parts"
        elif any(kw in msg for kw in ["중국", "lcsc", "jlc", "조달"]):
            task_type = "china_sourcing"
        elif any(kw in msg for kw in ["리뷰", "검토", "리스크", "위험"]):
            task_type = "review"
        elif any(kw in msg for kw in ["체크리스트", "테스트", "검증"]):
            task_type = "checklist"
        elif any(kw in msg for kw in ["비교", "차이", "vs"]):
            task_type = "compare"
        elif any(kw in msg for kw in ["리포트", "보고서", "정리"]):
            task_type = "report"

        agents_needed = []
        if any(kw in msg for kw in circuit_kw):
            agents_needed.append("CIRCUIT")
        if any(kw in msg for kw in rf_kw):
            agents_needed.append("RF")
        if any(kw in msg for kw in cert_kw):
            agents_needed.append("CERTIFICATION")
        multi = len(agents_needed) > 1

        return {
            "agent": agent,
            "task_type": task_type,
            "refined_query": message,
            "context_needed": ["past_projects", "knowledge_base"],
            "multi_agent": multi,
            "agents_needed": agents_needed if multi else [],
        }

    def _route_by_task_type(self, task_type: str, message: str) -> dict[str, Any]:
        """Route by explicit task type."""
        task_agent_map = {
            "import_metadata": "CIRCUIT",
            "search_summarize": "CIRCUIT",
            "design_draft": "CIRCUIT",
            "bom_normalize": "CIRCUIT",
            "substitute_parts": "CIRCUIT",
            "china_sourcing": "CIRCUIT",
            "review": "CIRCUIT",
            "checklist": "CERTIFICATION",
            "compare": "CIRCUIT",
            "report": "GENERAL",
            "mixed": "GENERAL",
            "unknown": "GENERAL",
        }
        return {
            "agent": task_agent_map.get(task_type, "GENERAL"),
            "task_type": task_type,
            "refined_query": message,
            "context_needed": ["past_projects", "knowledge_base"],
            "multi_agent": False,
            "agents_needed": [],
        }


def create_orchestrator() -> OrchestratorAgent:
    """Create and configure the orchestrator with all sub-agents."""
    from agents.circuit_agent import CircuitAgent
    from agents.rf_agent import RFAgent
    from agents.certification_agent import CertificationAgent
    from agents.mechanical_agent import MechanicalAgent
    from agents.general_agent import GeneralAgent

    orchestrator = OrchestratorAgent()
    orchestrator.register_agent(CircuitAgent())
    orchestrator.register_agent(RFAgent())
    orchestrator.register_agent(CertificationAgent())
    orchestrator.register_agent(MechanicalAgent())
    orchestrator.register_agent(GeneralAgent())

    return orchestrator
