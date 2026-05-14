"""Tests for EAIB (Embodied AI Brain) built-in subagent configurations.

Verifies that:
- All five brain-module subagent configs are importable and well-formed.
- They are registered in BUILTIN_SUBAGENTS under the expected names.
- Each config satisfies the SubagentConfig contract (required fields, types).
- The EAIB module registry (EAIB_SUBAGENTS) contains exactly the expected keys.
"""

from __future__ import annotations

import pytest

from deerflow.subagents.builtins import BUILTIN_SUBAGENTS
from deerflow.subagents.builtins.eaib import (
    EAIB_EXECUTIVE_CONFIG,
    EAIB_MEMORY_CONFIG,
    EAIB_MOTOR_CONFIG,
    EAIB_SAFETY_CONFIG,
    EAIB_SENSORY_CONFIG,
    EAIB_SUBAGENTS,
)
from deerflow.subagents.config import SubagentConfig

# ---------------------------------------------------------------------------
# Expected EAIB subagent names
# ---------------------------------------------------------------------------

EXPECTED_EAIB_NAMES = {
    "eaib-sensory",
    "eaib-motor",
    "eaib-memory",
    "eaib-safety",
    "eaib-executive",
}


# ---------------------------------------------------------------------------
# EAIB module registry
# ---------------------------------------------------------------------------


class TestEaibRegistry:
    def test_eaib_subagents_dict_has_all_modules(self):
        assert set(EAIB_SUBAGENTS.keys()) == EXPECTED_EAIB_NAMES

    def test_eaib_subagents_values_are_subagent_configs(self):
        for name, cfg in EAIB_SUBAGENTS.items():
            assert isinstance(cfg, SubagentConfig), f"{name} must be a SubagentConfig"

    def test_eaib_subagents_registered_in_builtin_subagents(self):
        for name in EXPECTED_EAIB_NAMES:
            assert name in BUILTIN_SUBAGENTS, f"'{name}' must appear in BUILTIN_SUBAGENTS"

    def test_builtin_subagents_still_includes_legacy_agents(self):
        assert "general-purpose" in BUILTIN_SUBAGENTS
        assert "bash" in BUILTIN_SUBAGENTS


# ---------------------------------------------------------------------------
# Per-config field validation — parametrised over all five modules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "config",
    [
        EAIB_SENSORY_CONFIG,
        EAIB_MOTOR_CONFIG,
        EAIB_MEMORY_CONFIG,
        EAIB_SAFETY_CONFIG,
        EAIB_EXECUTIVE_CONFIG,
    ],
    ids=["sensory", "motor", "memory", "safety", "executive"],
)
class TestEaibConfigContract:
    def test_name_is_non_empty_string(self, config: SubagentConfig):
        assert isinstance(config.name, str)
        assert config.name.strip()

    def test_name_uses_eaib_prefix(self, config: SubagentConfig):
        assert config.name.startswith("eaib-"), f"Name '{config.name}' must start with 'eaib-'"

    def test_description_is_non_empty_string(self, config: SubagentConfig):
        assert isinstance(config.description, str)
        assert config.description.strip()

    def test_system_prompt_is_non_empty_string(self, config: SubagentConfig):
        assert isinstance(config.system_prompt, str)
        assert config.system_prompt.strip()

    def test_model_is_inherit(self, config: SubagentConfig):
        assert config.model == "inherit"

    def test_max_turns_is_positive_int(self, config: SubagentConfig):
        assert isinstance(config.max_turns, int)
        assert config.max_turns > 0

    def test_timeout_seconds_is_positive_int(self, config: SubagentConfig):
        assert isinstance(config.timeout_seconds, int)
        assert config.timeout_seconds > 0

    def test_disallowed_tools_excludes_ask_clarification(self, config: SubagentConfig):
        if config.disallowed_tools is not None:
            assert "ask_clarification" in config.disallowed_tools, (
                f"{config.name}: 'ask_clarification' must be disallowed to prevent subagent stall"
            )

    def test_tools_is_none_or_list_of_strings(self, config: SubagentConfig):
        if config.tools is not None:
            assert isinstance(config.tools, list)
            for t in config.tools:
                assert isinstance(t, str)


# ---------------------------------------------------------------------------
# Module-specific checks
# ---------------------------------------------------------------------------


class TestSafetyModuleSpecifics:
    """Safety module has stricter constraints."""

    def test_task_not_in_safety_tools(self):
        """Safety module should not use 'task' to prevent recursive nesting."""
        if EAIB_SAFETY_CONFIG.tools is not None:
            assert "task" not in EAIB_SAFETY_CONFIG.tools

    def test_safety_system_prompt_mentions_halt(self):
        assert "HALT" in EAIB_SAFETY_CONFIG.system_prompt

    def test_safety_system_prompt_mentions_allow(self):
        assert "ALLOW" in EAIB_SAFETY_CONFIG.system_prompt


class TestExecutiveModuleSpecifics:
    """Executive module coordinates other modules."""

    def test_executive_has_task_tool(self):
        """Executive needs 'task' to delegate to other brain modules."""
        assert EAIB_EXECUTIVE_CONFIG.tools is not None
        assert "task" in EAIB_EXECUTIVE_CONFIG.tools

    def test_executive_max_turns_is_highest(self):
        """Executive coordinates long multi-step plans."""
        turns = [
            EAIB_SENSORY_CONFIG.max_turns,
            EAIB_MOTOR_CONFIG.max_turns,
            EAIB_MEMORY_CONFIG.max_turns,
            EAIB_SAFETY_CONFIG.max_turns,
        ]
        assert EAIB_EXECUTIVE_CONFIG.max_turns >= max(turns), (
            "Executive module should have the highest max_turns to orchestrate long plans"
        )

    def test_executive_system_prompt_mentions_safety(self):
        assert "eaib-safety" in EAIB_EXECUTIVE_CONFIG.system_prompt


class TestMemoryModuleSpecifics:
    def test_memory_system_prompt_mentions_episodic(self):
        assert "episodic" in EAIB_MEMORY_CONFIG.system_prompt.lower()

    def test_memory_system_prompt_mentions_semantic(self):
        assert "semantic" in EAIB_MEMORY_CONFIG.system_prompt.lower()


class TestSensoryModuleSpecifics:
    def test_sensory_system_prompt_mentions_confidence(self):
        assert "confidence" in EAIB_SENSORY_CONFIG.system_prompt.lower()


class TestMotorModuleSpecifics:
    def test_motor_system_prompt_mentions_safety(self):
        assert "safety" in EAIB_MOTOR_CONFIG.system_prompt.lower()
