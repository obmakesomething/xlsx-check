"""Base agent class for all domain-specific agents."""

from __future__ import annotations
import json
import logging
from typing import Any, Optional

from config import settings

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class providing common LLM interaction logic."""

    agent_type: str = "base"
    system_prompt: str = "You are a helpful assistant."

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize Anthropic client: {e}")
        return self._client

    async def run(
        self,
        user_message: str,
        context: str = "",
        history: Optional[list[dict[str, str]]] = None,
    ) -> dict[str, Any]:
        """Send a message to the LLM with the agent's system prompt and return structured result."""
        messages = []
        if history:
            messages.extend(history)

        content = user_message
        if context:
            content = f"[참고 컨텍스트]\n{context}\n\n[사용자 요청]\n{user_message}"

        messages.append({"role": "user", "content": content})

        if self.client is None:
            return self._fallback_response(user_message)

        try:
            response = self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=4096,
                system=self.system_prompt,
                messages=messages,
            )
            text = response.content[0].text
            return {
                "agent_type": self.agent_type,
                "content": text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            }
        except Exception as e:
            logger.error(f"Agent {self.agent_type} LLM call failed: {e}")
            return self._fallback_response(user_message)

    async def run_structured(
        self,
        user_message: str,
        context: str = "",
        output_schema_hint: str = "",
    ) -> dict[str, Any]:
        """Run agent and attempt to parse JSON from the response."""
        prompt = user_message
        if output_schema_hint:
            prompt += f"\n\n반드시 다음 JSON 스키마에 맞춰 응답하세요:\n{output_schema_hint}"

        result = await self.run(prompt, context=context)
        content = result.get("content", "")

        parsed = self._try_parse_json(content)
        if parsed is not None:
            result["structured"] = parsed

        return result

    def _try_parse_json(self, text: str) -> Optional[dict]:
        """Try to extract JSON from text."""
        # Try direct parse
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try to find JSON block in markdown
        import re
        patterns = [r"```json\s*(.*?)\s*```", r"```\s*(.*?)\s*```", r"(\{.*\})"]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except (json.JSONDecodeError, TypeError):
                    continue
        return None

    def _fallback_response(self, user_message: str) -> dict[str, Any]:
        """Return a fallback response when the LLM is unavailable."""
        return {
            "agent_type": self.agent_type,
            "content": (
                f"[{self.agent_type} 에이전트] API 키가 설정되지 않았거나 LLM 호출에 실패했습니다. "
                f"요청 내용: {user_message[:200]}"
            ),
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "fallback": True,
        }
