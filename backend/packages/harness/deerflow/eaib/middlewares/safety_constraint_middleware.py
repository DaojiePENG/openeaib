"""Safety Constraint Middleware.

杏仁核 (Amygdala): intercepts tool calls before execution, evaluates risk,
and either blocks or requests user clarification for dangerous actions.

Positioned before ClarificationMiddleware so its clarification requests are
handled correctly by the existing interrupt mechanism.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphBubbleUp
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command
from langgraph.runtime import Runtime

from deerflow.agents.features import Prev
from deerflow.agents.middlewares.clarification_middleware import ClarificationMiddleware
from deerflow.eaib.amygdala.risk_assessor import RiskAssessment, get_risk_assessor
from deerflow.eaib.amygdala.safety_rules import RiskLevel

logger = logging.getLogger(__name__)

_BLOCKED_TOOL_CALL_ID_PREFIX = "safety_blocked_"


@Prev(ClarificationMiddleware)
class SafetyConstraintMiddleware(AgentMiddleware[AgentState]):
    """Intercepts tool calls and enforces safety rules.

    Decision table:
    - SAFE / LOW  → allow through unchanged
    - MEDIUM      → inject an ask_clarification tool call so the user confirms
    - HIGH        → same as MEDIUM but with stronger warning language
    - BLOCKED     → return a ToolMessage error immediately, tool never runs
    """

    state_schema = AgentState

    def _build_blocked_message(self, request: ToolCallRequest, assessment: RiskAssessment) -> ToolMessage:
        tool_name = str(request.tool_call.get("name") or "unknown_tool")
        tool_call_id = str(request.tool_call.get("id") or f"{_BLOCKED_TOOL_CALL_ID_PREFIX}{tool_name}")
        content = (
            f"[SAFETY BLOCK] Tool '{tool_name}' was blocked by the Amygdala safety system.\n"
            f"Reason: {assessment.reason}\n"
            f"Risk level: {assessment.risk_level.value}\n"
            "This action cannot be performed. Please choose a different approach."
        )
        return ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
            name=tool_name,
            status="error",
        )

    def _evaluate(self, request: ToolCallRequest) -> RiskAssessment:
        tool_name = str(request.tool_call.get("name") or "")
        tool_args = request.tool_call.get("args") or {}
        assessor = get_risk_assessor()
        return assessor.assess_tool_call(tool_name=tool_name, tool_args=tool_args)

    @override
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        try:
            assessment = self._evaluate(request)
        except Exception as exc:
            logger.warning("SafetyConstraintMiddleware: risk assessment failed for %s: %s", request.tool_call.get("name"), exc)
            return handler(request)

        if assessment.risk_level == RiskLevel.BLOCKED:
            logger.warning("SafetyConstraintMiddleware: BLOCKED tool=%s reason=%s", request.tool_call.get("name"), assessment.reason)
            return self._build_blocked_message(request, assessment)

        if assessment.requires_clarification:
            logger.info("SafetyConstraintMiddleware: HIGH/MEDIUM risk for tool=%s — requesting clarification", request.tool_call.get("name"))
            # Signal to the lead agent that clarification is needed.
            # We return a ToolMessage with a special sentinel so the agent knows to ask.
            tool_call_id = str(request.tool_call.get("id") or f"safety_{request.tool_call.get('name')}")
            return ToolMessage(
                content=(
                    f"[SAFETY CHECK REQUIRED] {assessment.to_prompt_fragment()}\n"
                    "Please ask the user for explicit confirmation before proceeding with this action."
                ),
                tool_call_id=tool_call_id,
                name=str(request.tool_call.get("name") or "unknown"),
                status="error",
            )

        return handler(request)

    @override
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        try:
            assessment = self._evaluate(request)
        except Exception as exc:
            logger.warning("SafetyConstraintMiddleware: risk assessment failed: %s", exc)
            return await handler(request)

        if assessment.risk_level == RiskLevel.BLOCKED:
            logger.warning("SafetyConstraintMiddleware: BLOCKED tool=%s", request.tool_call.get("name"))
            return self._build_blocked_message(request, assessment)

        if assessment.requires_clarification:
            tool_call_id = str(request.tool_call.get("id") or f"safety_{request.tool_call.get('name')}")
            return ToolMessage(
                content=(
                    f"[SAFETY CHECK REQUIRED] {assessment.to_prompt_fragment()}\n"
                    "Please ask the user for explicit confirmation before proceeding with this action."
                ),
                tool_call_id=tool_call_id,
                name=str(request.tool_call.get("name") or "unknown"),
                status="error",
            )

        try:
            return await handler(request)
        except GraphBubbleUp:
            raise
