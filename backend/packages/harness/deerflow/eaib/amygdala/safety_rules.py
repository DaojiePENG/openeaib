"""Safety rules for the Amygdala module (杏仁核).

Defines structured risk categories for robotic actions.
Rules are evaluated in order; first match wins.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"
    """BLOCKED = permanently refused; user cannot override in this session."""


@dataclass
class SafetyRule:
    """A single safety evaluation rule."""

    rule_id: str
    description: str
    risk_level: RiskLevel
    patterns: list[re.Pattern[str]] = field(default_factory=list)
    """Regex patterns matched against the normalized action text."""
    predicate: Callable[[str, dict], bool] | None = None
    """Optional Python predicate for complex contextual checks.
    Receives (action_text: str, context: dict) → bool."""
    advice: str = ""
    """Suggested alternative or clarifying question shown to the user."""


# ---------------------------------------------------------------------------
# Rule library
# ---------------------------------------------------------------------------

SAFETY_RULES: list[SafetyRule] = [
    # ---- BLOCKED: irreversible destructive actions ----
    SafetyRule(
        rule_id="block_system_destroy",
        description="Destroy or format the operating system / primary storage",
        risk_level=RiskLevel.BLOCKED,
        patterns=[
            re.compile(r"\b(mkfs|format|fdisk|parted)\b.*(/dev/sd[a-z]|nvme0)"),
            re.compile(r"rm\s+-rf\s+(/\s*$|/\*|\s*/home|\s*/root)"),
        ],
        advice="This action would destroy the operating system and is permanently blocked.",
    ),
    SafetyRule(
        rule_id="block_emergency_override",
        description="Override robot emergency-stop system",
        risk_level=RiskLevel.BLOCKED,
        patterns=[
            re.compile(r"disable\s+(emergency|e-stop|estop)", re.IGNORECASE),
            re.compile(r"bypass\s+safety", re.IGNORECASE),
        ],
        advice="Bypassing emergency-stop systems is permanently blocked.",
    ),

    # ---- HIGH: physical danger to robot or people ----
    SafetyRule(
        rule_id="high_obstacle_detected",
        description="Movement command with known obstacle in path",
        risk_level=RiskLevel.HIGH,
        patterns=[
            re.compile(r"(move|walk|go|drive|step)\s+(forward|ahead|front)", re.IGNORECASE),
            re.compile(r"(move|walk)\s+\d+(\.\d+)?\s*(m|meter|metre)", re.IGNORECASE),
        ],
        advice="An obstacle may be in the path. Please confirm the area is clear, or specify a different direction.",
    ),
    SafetyRule(
        rule_id="high_max_joint_velocity",
        description="Set joint velocity above safe threshold",
        risk_level=RiskLevel.HIGH,
        patterns=[
            re.compile(r"(set|apply).*velocity.*[5-9]\d{1,2}|[1-9]\d{3,}", re.IGNORECASE),
            re.compile(r"joint.*speed.*(fast|max|full|100%)", re.IGNORECASE),
        ],
        advice="High joint velocities risk mechanical damage or injury. Confirm the velocity limit is safe.",
    ),
    SafetyRule(
        rule_id="high_unattended_locomotion",
        description="Extended autonomous locomotion without human supervision",
        risk_level=RiskLevel.HIGH,
        patterns=[
            re.compile(r"(walk|run|move|drive)\s+autonomously\s+for\s+\d+\s*(minutes?|hours?)", re.IGNORECASE),
        ],
        advice="Long autonomous locomotion requires confirming no humans or fragile objects are in the area.",
    ),

    # ---- MEDIUM: reversible but potentially disruptive ----
    SafetyRule(
        rule_id="medium_install_package",
        description="Install software packages on the robot system",
        risk_level=RiskLevel.MEDIUM,
        patterns=[
            re.compile(r"(pip|pip3|conda)\s+install", re.IGNORECASE),
            re.compile(r"apt(-get)?\s+install", re.IGNORECASE),
        ],
        advice="Installing packages modifies the system. Confirm the package name is correct.",
    ),
    SafetyRule(
        rule_id="medium_network_config",
        description="Modify network configuration",
        risk_level=RiskLevel.MEDIUM,
        patterns=[
            re.compile(r"(ifconfig|ip\s+addr|nmcli)\s+(add|delete|set|up|down)", re.IGNORECASE),
        ],
        advice="Changing network settings may disconnect the robot. Confirm you have physical access.",
    ),
    SafetyRule(
        rule_id="medium_unknown_motion",
        description="Generic motion command without explicit parameters",
        risk_level=RiskLevel.MEDIUM,
        patterns=[
            re.compile(r"\b(move|walk|jump|kick|punch|grab|push)\b", re.IGNORECASE),
        ],
        advice="Please specify direction, distance, and speed to ensure safe execution.",
    ),

    # ---- LOW: worth logging but auto-allowed ----
    SafetyRule(
        rule_id="low_sensor_read",
        description="Read sensor data",
        risk_level=RiskLevel.LOW,
        patterns=[
            re.compile(r"(read|get|capture|record)\s+(sensor|camera|imu|lidar|image|frame)", re.IGNORECASE),
        ],
    ),
    SafetyRule(
        rule_id="low_diagnostic",
        description="Run diagnostics or status check",
        risk_level=RiskLevel.LOW,
        patterns=[
            re.compile(r"(check|diagnose|test|ping|status|health)", re.IGNORECASE),
        ],
    ),
]
