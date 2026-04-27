"""Smoke test for make_eaib_agent.

Verifies that the EAIB agent factory can be imported and called without
errors, and that the returned object has the expected LangGraph interface.
We mock the heavy LLM / tool dependencies so the test runs without network
access or API keys.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Pre-mock the LangGraph / LangChain objects that hit external services
# ---------------------------------------------------------------------------

# Mock create_chat_model to return a MagicMock (avoids API key checks)
_fake_model = MagicMock()
_fake_model.bind_tools.return_value = _fake_model

# Mock create_agent to return a simple callable with a known attribute
_fake_graph = MagicMock()
_fake_graph.name = "eaib_agent"


@pytest.fixture(autouse=True)
def _patch_heavyweights(monkeypatch):
    """Replace external dependencies with lightweight mocks."""
    with (
        patch("deerflow.models.create_chat_model", return_value=_fake_model),
        patch("langchain.agents.create_agent", return_value=_fake_graph),
        patch("deerflow.tools.get_available_tools", return_value=[]),
        patch("deerflow.agents.lead_agent.agent._build_middlewares", return_value=[]),
        patch("deerflow.agents.lead_agent.agent._get_runtime_config", return_value={}),
        patch("deerflow.agents.lead_agent.agent._resolve_model_name", return_value="fake-model"),
    ):
        yield


def test_make_eaib_agent_importable():
    """make_eaib_agent should be importable from the registered entry point."""
    from deerflow.eaib.agents import make_eaib_agent  # noqa: F401

    assert callable(make_eaib_agent)


def test_make_eaib_agent_returns_graph():
    """make_eaib_agent(config) should return a LangGraph-compatible object."""
    from deerflow.eaib.agents import make_eaib_agent

    config = {"configurable": {"thread_id": "test-thread"}}
    result = make_eaib_agent(config)
    # Should return the object produced by create_agent (mocked as _fake_graph)
    assert result is _fake_graph


def test_eaib_state_schema():
    """EAIBState should extend ThreadState and expose EAIB-specific fields."""
    from deerflow.eaib.state import EAIBState

    fields = EAIBState.__annotations__
    assert "body_state" in fields
    assert "skill_context" in fields
    assert "safety_flags" in fields


def test_eaib_tools_list():
    """ALL_EAIB_TOOLS and PERCEPTION_TOOLS should be non-empty lists."""
    from deerflow.eaib.tools import ALL_EAIB_TOOLS
    from deerflow.eaib.occipital_parietal import PERCEPTION_TOOLS

    assert isinstance(ALL_EAIB_TOOLS, list)
    assert len(ALL_EAIB_TOOLS) > 0
    assert isinstance(PERCEPTION_TOOLS, list)
    assert len(PERCEPTION_TOOLS) > 0


def test_middleware_classes_importable():
    """All three EAIB middlewares should be importable."""
    from deerflow.eaib.middlewares import (  # noqa: F401
        BodyAwarenessMiddleware,
        SafetyConstraintMiddleware,
        SkillInjectionMiddleware,
    )
