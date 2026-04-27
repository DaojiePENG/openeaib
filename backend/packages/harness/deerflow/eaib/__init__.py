"""OpenEAIB — Embodied AI Brain (具身智脑).

Top-level package for the EAIB extension on top of DeerFlow.
Brain-inspired modular multi-agent system for embodied robotics.
"""

from deerflow.eaib.state.eaib_state import (
    BodyState,
    EAIBState,
    SensorInfo,
    SensorMap,
    SkillContext,
)

__all__ = [
    "EAIBState",
    "BodyState",
    "SensorInfo",
    "SensorMap",
    "SkillContext",
]
