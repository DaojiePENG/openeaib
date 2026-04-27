"""EAIB lead agent factory.

前额叶皮层 (Prefrontal Cortex): make_eaib_agent() factory wired to LangGraph.

Registered in langgraph.json as:
  "eaib_agent": "deerflow.eaib.agents:make_eaib_agent"
"""

from __future__ import annotations

import logging

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig

from deerflow.agents.lead_agent.agent import _build_middlewares, _get_runtime_config, _resolve_model_name
from deerflow.agents.middlewares.tool_error_handling_middleware import build_lead_runtime_middlewares
from deerflow.eaib.agents.eaib_prompt import build_eaib_system_prompt
from deerflow.eaib.middlewares import (
    BodyAwarenessMiddleware,
    SafetyConstraintMiddleware,
    SkillInjectionMiddleware,
)
from deerflow.eaib.state import EAIBState
from deerflow.models import create_chat_model

logger = logging.getLogger(__name__)


def _build_eaib_middlewares(config: RunnableConfig, model_name: str | None) -> list:
    """Build the EAIB middleware chain.

    Extends the base DeerFlow chain with three EAIB-specific middlewares:
    - BodyAwarenessMiddleware  — injected after ThreadDataMiddleware via @Next
    - SafetyConstraintMiddleware — injected before ClarificationMiddleware via @Prev
    - SkillInjectionMiddleware   — injected before ClarificationMiddleware via @Prev

    The extra_middleware kwarg in _build_middlewares handles @Next/@Prev positioning.
    """
    eaib_extras = [
        BodyAwarenessMiddleware(),
        SafetyConstraintMiddleware(),
        SkillInjectionMiddleware(),
    ]
    return _build_middlewares(config, model_name=model_name, custom_middlewares=eaib_extras)


def make_eaib_agent(config: RunnableConfig):
    """Factory function called by LangGraph to create the EAIB lead agent."""
    from deerflow.tools import get_available_tools

    cfg = _get_runtime_config(config)
    requested_model_name: str | None = cfg.get("model_name") or cfg.get("model")
    subagent_enabled: bool = cfg.get("subagent_enabled", False)
    model_name = _resolve_model_name(requested_model_name)

    # Inject run metadata
    if "metadata" not in config:
        config["metadata"] = {}
    config["metadata"].update({
        "agent_name": "eaib",
        "model_name": model_name or "default",
    })

    # Combine DeerFlow tools with all EAIB-specific tools
    from deerflow.eaib.tools import ALL_EAIB_TOOLS
    from deerflow.eaib.occipital_parietal import PERCEPTION_TOOLS

    tools = (
        get_available_tools(model_name=model_name, subagent_enabled=subagent_enabled)
        + ALL_EAIB_TOOLS
        + PERCEPTION_TOOLS
    )

    system_prompt = build_eaib_system_prompt()

    return create_agent(
        model=create_chat_model(name=model_name),
        tools=tools,
        middleware=_build_eaib_middlewares(config, model_name=model_name),
        system_prompt=system_prompt,
        state_schema=EAIBState,
    )
