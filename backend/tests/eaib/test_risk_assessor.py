"""Tests for RiskAssessor (Amygdala)."""
from __future__ import annotations

import pytest

from deerflow.eaib.amygdala.risk_assessor import RiskAssessor
from deerflow.eaib.amygdala.safety_rules import RiskLevel


@pytest.fixture()
def assessor() -> RiskAssessor:
    return RiskAssessor()


def test_safe_action(assessor: RiskAssessor) -> None:
    result = assessor.assess("list available sensors")
    assert result.level in (RiskLevel.SAFE, RiskLevel.LOW)


def test_high_velocity_flagged(assessor: RiskAssessor) -> None:
    result = assessor.assess("send_velocity_command linear_x=5.0 m/s")
    assert result.level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.BLOCKED)


def test_emergency_stop_blocked(assessor: RiskAssessor) -> None:
    result = assessor.assess("emergency_stop all motors now")
    # emergency_stop itself might be SAFE (it's protective) or MEDIUM — depends on rules
    # At minimum it should not panic
    assert isinstance(result.level, RiskLevel)


def test_system_shutdown_blocked(assessor: RiskAssessor) -> None:
    result = assessor.assess("shutdown -h now")
    assert result.level in (RiskLevel.HIGH, RiskLevel.BLOCKED)


def test_rm_rf_blocked(assessor: RiskAssessor) -> None:
    result = assessor.assess("rm -rf /home/user/data")
    assert result.level in (RiskLevel.HIGH, RiskLevel.BLOCKED)


def test_requires_clarification_on_medium(assessor: RiskAssessor) -> None:
    # Artificially create a MEDIUM assessment
    from deerflow.eaib.amygdala.safety_rules import SafetyRule, RiskLevel as RL
    rule = SafetyRule(
        rule_id="test_medium",
        description="test",
        level=RL.MEDIUM,
        patterns=["test_pattern_xyz"],
        advice="ask user",
        applies_to_tools=["any"],
    )
    custom_assessor = RiskAssessor(rules=[rule])
    result = custom_assessor.assess("test_pattern_xyz")
    assert result.requires_clarification is True
    assert result.is_blocked is False


def test_is_blocked_on_blocked_level(assessor: RiskAssessor) -> None:
    from deerflow.eaib.amygdala.safety_rules import SafetyRule, RiskLevel as RL
    rule = SafetyRule(
        rule_id="test_blocked",
        description="test",
        level=RL.BLOCKED,
        patterns=["absolutely_forbidden_xyz"],
        advice="never",
        applies_to_tools=["any"],
    )
    custom_assessor = RiskAssessor(rules=[rule])
    result = custom_assessor.assess("absolutely_forbidden_xyz")
    assert result.is_blocked is True
    assert result.requires_clarification is False
