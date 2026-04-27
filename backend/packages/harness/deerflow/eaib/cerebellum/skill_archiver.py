"""SkillArchiver — moves obsolete skills to the archive (graveyard).

小脑 (Cerebellum): skill retirement and garbage collection.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from deerflow.eaib.cerebellum.skill_registry import SkillRegistry, get_skill_registry
from deerflow.eaib.cerebellum.skill_types import RobotSkill, SkillStatus

logger = logging.getLogger(__name__)


class SkillArchiver:
    """Manages the archival lifecycle of robot skills."""

    def __init__(self, registry: SkillRegistry | None = None) -> None:
        self._registry = registry or get_skill_registry()

    def archive_superseded(self, old_skill_id: str, new_skill_id: str, reason: str | None = None) -> bool:
        """Archive an old skill that has been superseded by a newer version."""
        msg = reason or f"Superseded by {new_skill_id}"
        return self._registry.archive_skill(old_skill_id, reason=msg, superseded_by=new_skill_id)

    def archive_broken(self, skill_id: str, reason: str = "Skill consistently fails execution") -> bool:
        """Archive a skill that has a critically low success rate."""
        return self._registry.archive_skill(skill_id, reason=reason)

    def archive_by_user(self, skill_id: str, reason: str = "Archived by user request") -> bool:
        """Explicitly archive a skill at user or agent request."""
        return self._registry.archive_skill(skill_id, reason=reason)

    def run_garbage_collection(
        self,
        body_id: str | None = None,
        min_usage_for_gc: int = 5,
        low_success_threshold: float = 0.2,
        max_stable_skills_per_body: int = 200,
    ) -> list[str]:
        """Automatically archive underperforming or excess skills.

        Args:
            body_id: Scope GC to a specific body. None = all bodies.
            min_usage_for_gc: Skills with fewer executions than this are skipped (not enough data).
            low_success_threshold: Archive TESTED/STABLE skills below this success rate.
            max_stable_skills_per_body: When a body has more stable skills than this,
                                        archive the oldest by last usage.

        Returns:
            List of archived skill_ids.
        """
        archived: list[str] = []

        candidates = self._registry.list_all(include_archived=False)
        if body_id:
            candidates = [s for s in candidates if s.body_id in (body_id, "universal")]

        # Archive chronically failing skills
        for skill in candidates:
            if skill.usage_count >= min_usage_for_gc and skill.success_rate < low_success_threshold:
                reason = (
                    f"Low success rate ({skill.success_rate:.0%} over {skill.usage_count} executions)"
                )
                self._registry.archive_skill(skill.skill_id, reason=reason)
                archived.append(skill.skill_id)
                logger.info("GC archived failing skill: %s", skill.skill_id)

        # Trim excess stable skills per body
        all_bodies = {s.body_id for s in self._registry.list_all()}
        for bid in all_bodies:
            if body_id and bid != body_id:
                continue
            stable = self._registry.list_stable(body_id=bid)
            # Only body-specific stable skills count toward the per-body limit
            body_stable = [s for s in stable if s.body_id == bid]
            if len(body_stable) > max_stable_skills_per_body:
                # Sort by usage_count ascending (least used first)
                body_stable.sort(key=lambda s: s.usage_count)
                excess = body_stable[: len(body_stable) - max_stable_skills_per_body]
                for skill in excess:
                    self._registry.archive_skill(
                        skill.skill_id,
                        reason=f"Trimmed by GC: body skill limit ({max_stable_skills_per_body}) reached",
                    )
                    archived.append(skill.skill_id)
                    logger.info("GC trimmed excess stable skill: %s", skill.skill_id)

        return archived
