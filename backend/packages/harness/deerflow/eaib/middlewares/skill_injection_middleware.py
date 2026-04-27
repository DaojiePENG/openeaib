"""Skill Injection Middleware.

小脑 (Cerebellum): injects a summary of available robot skills into the model's
context before each turn so the agent can reference them without an explicit
tool call.

Positioned before ClarificationMiddleware (Prev) so skill context is available
when the model decides whether to use a skill or generate new code.
"""

from __future__ import annotations

import logging
from typing import Any, NotRequired, override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import SystemMessage
from langgraph.runtime import Runtime

from deerflow.agents.features import Prev
from deerflow.agents.middlewares.clarification_middleware import ClarificationMiddleware
from deerflow.eaib.cerebellum.skill_registry import get_skill_registry

logger = logging.getLogger(__name__)

_SKILL_CONTEXT_PREFIX = "eaib_skill_context"


class SkillInjectionState(AgentState):
    """Compatible with EAIBState schema."""

    body_state: NotRequired[dict | None]


@Prev(ClarificationMiddleware)
class SkillInjectionMiddleware(AgentMiddleware[SkillInjectionState]):
    """Prepends a skill summary system message before each model call.

    Reads body_id from body_state injected by BodyAwarenessMiddleware.
    Falls back to 'host' if no body_state is present.
    """

    state_schema = SkillInjectionState

    def _get_skill_summary(self, state: SkillInjectionState) -> str | None:
        body_state = state.get("body_state")
        body_id: str = (body_state or {}).get("body_id", "host")

        try:
            registry = get_skill_registry()
            summary = registry.summary_for_prompt(body_id=body_id)
            return summary if summary.strip() else None
        except Exception as exc:
            logger.warning("SkillInjectionMiddleware: could not build skill summary: %s", exc)
            return None

    @override
    def before_model(self, state: SkillInjectionState, runtime: Runtime) -> dict[str, Any] | None:
        summary = self._get_skill_summary(state)
        if not summary:
            return None

        msg = SystemMessage(
            content=summary,
            id=_SKILL_CONTEXT_PREFIX,
        )
        # Inject at the front of messages so it appears as early context
        existing = list(state.get("messages", []))
        return {"messages": [msg] + existing}
