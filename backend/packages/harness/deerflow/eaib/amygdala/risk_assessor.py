"""RiskAssessor — dual-path (rule + LLM) risk evaluation for the Amygdala.

杏仁核 (Amygdala): assess risk of any proposed robot action.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from deerflow.eaib.amygdala.safety_rules import SAFETY_RULES, RiskLevel, SafetyRule

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessment:
    """Result of a risk evaluation."""

    level: RiskLevel
    triggered_rule: SafetyRule | None
    action_text: str
    advice: str
    explanation: str

    @property
    def requires_clarification(self) -> bool:
        return self.level in (RiskLevel.MEDIUM, RiskLevel.HIGH)

    @property
    def is_blocked(self) -> bool:
        return self.level == RiskLevel.BLOCKED

    def to_prompt_fragment(self) -> str:
        """Format for injection into clarification question."""
        parts = [f"**Risk level**: {self.level.value}", f"**Reason**: {self.explanation}"]
        if self.advice:
            parts.append(f"**Advice**: {self.advice}")
        return "\n".join(parts)


class RiskAssessor:
    """Evaluates the risk level of a proposed robotic action.

    Uses a two-path approach:
    1. Fast rule-based scan (regex patterns in SAFETY_RULES)
    2. If no rule matches, classify as SAFE/LOW by default with optional LLM escalation

    The LLM path is intentionally *not* invoked for every action to keep latency low.
    It is only used for ambiguous HIGH-risk candidates that fail the pattern check.
    """

    def __init__(self, rules: list[SafetyRule] | None = None) -> None:
        self._rules = rules if rules is not None else SAFETY_RULES

    def assess(self, action_text: str, context: dict | None = None) -> RiskAssessment:
        """Evaluate the risk of ``action_text``.

        Args:
            action_text: Natural language description of the intended action.
            context: Optional dict with keys like ``body_type``, ``sensor_data``,
                     ``nearby_obstacles``, etc.

        Returns:
            RiskAssessment with level, triggered rule, and advice.
        """
        ctx = context or {}
        normalized = action_text.lower()

        for rule in self._rules:
            matched = False

            # Check regex patterns
            for pattern in rule.patterns:
                if pattern.search(normalized):
                    matched = True
                    break

            # Check optional predicate
            if not matched and rule.predicate is not None:
                try:
                    matched = rule.predicate(normalized, ctx)
                except Exception:
                    logger.exception("Safety rule predicate %s raised an error", rule.rule_id)

            if matched:
                explanation = f"Action matches safety rule '{rule.rule_id}': {rule.description}."
                logger.info(
                    "Safety assessment: %s → %s (rule=%s)",
                    action_text[:80],
                    rule.risk_level.value,
                    rule.rule_id,
                )
                return RiskAssessment(
                    level=rule.risk_level,
                    triggered_rule=rule,
                    action_text=action_text,
                    advice=rule.advice,
                    explanation=explanation,
                )

        # No rule matched — default to SAFE
        return RiskAssessment(
            level=RiskLevel.SAFE,
            triggered_rule=None,
            action_text=action_text,
            advice="",
            explanation="No safety rules were triggered.",
        )

    def assess_tool_call(self, tool_name: str, tool_args: dict) -> RiskAssessment:
        """Convenience wrapper for assessing a tool call.

        Reconstructs a plain-text description from the tool name + args and
        delegates to ``assess()``.
        """
        args_str = " ".join(f"{k}={v}" for k, v in tool_args.items())
        action_text = f"{tool_name} {args_str}".strip()
        return self.assess(action_text, context={"tool_name": tool_name, "tool_args": tool_args})


# Singleton
_assessor: RiskAssessor | None = None


def get_risk_assessor() -> RiskAssessor:
    global _assessor
    if _assessor is None:
        _assessor = RiskAssessor()
    return _assessor
