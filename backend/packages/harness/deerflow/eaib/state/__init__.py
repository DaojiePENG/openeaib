"""EAIBState — extended LangGraph state schema for the Embodied AI Brain.

Extends DeerFlow's ThreadState with:
- body_state: current robot body identity and sensor manifest
- sensor_map: live sensor readings injected by BodyAwarenessMiddleware
- active_skills_context: condensed descriptions of matched robot skills
- safety_flags: safety constraint signals from AmygdalaMiddleware
"""

from typing import Annotated, NotRequired, TypedDict

from deerflow.agents.thread_state import ThreadState


# ---------------------------------------------------------------------------
# Sub-types
# ---------------------------------------------------------------------------


class SensorInfo(TypedDict):
    """Description of a single sensor/peripheral."""

    name: str
    """Human-readable name, e.g. 'front_camera'."""
    sensor_type: str
    """Type: 'camera' | 'lidar' | 'imu' | 'microphone' | 'speaker' | 'joint_encoder' | 'odometer' | 'gpu' | 'other'."""
    device_path: str | None
    """OS device path, e.g. '/dev/video0'. None for virtual/software sensors."""
    ros_topic: str | None
    """ROS2 topic, e.g. '/camera/image_raw'. None if not ROS-based."""
    available: bool
    """Whether the sensor is currently reachable."""
    extra: dict
    """Additional metadata (resolution, frame_rate, etc.)."""


class SensorMap(TypedDict):
    """Snapshot of all detected sensors keyed by sensor name."""

    sensors: list[SensorInfo]
    scanned_at: str
    """ISO-8601 UTC timestamp of last scan."""


class BodyState(TypedDict):
    """Current robot body identity and hardware context."""

    body_id: str
    """Unique identifier, e.g. 'unitree_g1', 'unitree_go2', 'host'."""
    body_name: str
    """Display name, e.g. 'Unitree G1 Humanoid'."""
    body_type: str
    """Classification: 'humanoid' | 'quadruped' | 'arm' | 'wheeled' | 'host' | 'unknown'."""
    sdks: list[str]
    """Installed SDK identifiers, e.g. ['unitree_sdk2py']."""
    sensor_map: SensorMap | None
    """Latest sensor snapshot."""


class SkillContext(TypedDict):
    """Condensed context about available robot skills for the current body."""

    matched_skills: list[str]
    """Names of skills matching the current body_id."""
    skill_summaries: str
    """Formatted string of skill names + one-line descriptions for prompt injection."""
    total_stable_skills: int
    """Number of stable skills for the current body."""
    total_universal_skills: int
    """Number of stable universal skills."""


def _merge_body_state(existing: BodyState | None, new: BodyState | None) -> BodyState | None:
    """Reducer: later write wins."""
    if new is None:
        return existing
    return new


def _merge_skill_context(existing: SkillContext | None, new: SkillContext | None) -> SkillContext | None:
    """Reducer: later write wins."""
    if new is None:
        return existing
    return new


def _merge_safety_flags(existing: dict | None, new: dict | None) -> dict:
    """Reducer: merge safety flag dicts; new values override existing."""
    if existing is None:
        return new or {}
    if new is None:
        return existing
    return {**existing, **new}


# ---------------------------------------------------------------------------
# Extended state schema
# ---------------------------------------------------------------------------


class EAIBState(ThreadState):
    """Full EAIB state schema.

    Extends DeerFlow's ThreadState with robotics-specific fields that are
    populated by EAIB middlewares and injected into agent prompts.
    """

    body_state: Annotated[BodyState | None, _merge_body_state]
    """Current robot body, populated by BodyAwarenessMiddleware."""

    skill_context: Annotated[SkillContext | None, _merge_skill_context]
    """Matched skill summaries for this body, populated by SkillInjectionMiddleware."""

    safety_flags: Annotated[dict, _merge_safety_flags]
    """Active safety constraints, populated by SafetyConstraintMiddleware."""
