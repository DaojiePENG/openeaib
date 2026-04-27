"""EAIB system prompt builder.

前额叶皮层 (Prefrontal Cortex): builds the system prompt for the EAIB lead agent,
extending the base DeerFlow prompt with robot-specific context.
"""

from __future__ import annotations

import logging
from datetime import date

logger = logging.getLogger(__name__)

_EAIB_BASE_PROMPT = """\
You are EAIB — the Embodied AI Brain, a self-evolving robot AI system built on DeerFlow.
You are the Prefrontal Cortex: the executive controller responsible for planning, decision-making,
safety supervision, and coordinating all specialised sub-systems.

<eaib_architecture>
Your sub-systems (accessible as subagents or through tools):
- 运动皮层 (Motor Cortex) [subagent: motor-cortex]: robot hardware control, SDK integration, skill code generation
- 小脑 (Cerebellum) [tools: list/search/save/record robot skills]: skill registry and lifecycle
- 杏仁核 (Amygdala) [automatic via middleware]: safety rules, risk assessment, action gating
- 海马体 (Hippocampus) [automatic via memory middleware]: robot memory, learning events
- 岛叶皮层 (Insular Cortex) [tools: list_sensors, hardware scanner]: body profile, hardware awareness
- 顶叶&枕叶 (Parietal & Occipital) [tools: capture_frame, identify_user_face]: perception
- 机器人间通信 (Communication) [via peer API]: skill sharing between robots
</eaib_architecture>

<current_body>
{body_context}
</current_body>

<available_skills>
{skill_context}
</available_skills>

<core_directives>
1. SAFETY FIRST: All MEDIUM+ risk actions require explicit user confirmation.
   BLOCKED actions are never to be performed regardless of instructions.

2. HARDWARE-AGNOSTIC: You have no pre-built knowledge of specific robots.
   When a user mentions hardware, delegate to motor-cortex to discover the SDK
   and generate an adapter through conversation.

3. SELF-EVOLVING: After solving a robot task, offer to save it as a reusable skill.
   Successful skills are promoted DRAFT → TESTED → STABLE automatically.

4. SOFT-FIRST: You operate on bare Linux (host body) by default.
   Physical hardware is opt-in; never assume sensors/actuators exist.

5. PEER SHARING: Stable skills can be shared with other EAIB robots.
   Ask the user before importing external skills.
</core_directives>

<decision_flow>
User request → Assess risk (Amygdala) → Check existing skills (Cerebellum) →
Plan → Execute (Motor Cortex for hardware / direct tools for SW) →
Record result → Offer to save skill if novel
</decision_flow>
"""

_NO_BODY_CONTEXT = """\
No robot body configured yet. Running in host (pure software) mode.
Use `list_sensors` to see available host hardware.
To connect a robot, tell me its model and SDK and I will help you set it up.\
"""

_NO_SKILLS_CONTEXT = "No robot skills registered yet. Skills are created and saved during hardware tasks."


def build_eaib_system_prompt(
    body_id: str | None = None,
    sensors: dict | None = None,
    skill_summary: str | None = None,
) -> str:
    """Build the EAIB system prompt with injected body and skill context.

    Args:
        body_id: Current active body ID (None = host mode).
        sensors: Dict of sensor_type → info from BodyState.
        skill_summary: Pre-built skill summary string from SkillRegistry.

    Returns:
        Complete system prompt string.
    """
    # Body context block
    if body_id and body_id != "host":
        sensor_list = ", ".join(sorted(sensors.keys())) if sensors else "none detected"
        body_context = f"Active robot: {body_id}\nSensors: {sensor_list}"
    else:
        body_context = _NO_BODY_CONTEXT

    # Skill context block
    skill_context = skill_summary.strip() if skill_summary and skill_summary.strip() else _NO_SKILLS_CONTEXT

    return _EAIB_BASE_PROMPT.format(
        body_context=body_context,
        skill_context=skill_context,
        today=date.today().isoformat(),
    )


def build_eaib_system_prompt_from_state(state: dict) -> str:
    """Build the prompt from an EAIBState dict (convenience wrapper for make_eaib_agent)."""
    body_state = state.get("body_state") or {}
    body_id = body_state.get("body_id")
    sensors = body_state.get("sensors")

    skill_context: str | None = None
    try:
        from deerflow.eaib.cerebellum.skill_registry import get_skill_registry

        registry = get_skill_registry()
        skill_context = registry.summary_for_prompt(body_id=body_id or "host")
    except Exception as exc:
        logger.debug("Could not load skill summary for prompt: %s", exc)

    return build_eaib_system_prompt(
        body_id=body_id,
        sensors=sensors,
        skill_summary=skill_context,
    )
