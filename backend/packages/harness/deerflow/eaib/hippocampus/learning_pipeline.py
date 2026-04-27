"""LearningPipeline — listens for skill lifecycle events and triggers consolidation.

海马体 (Hippocampus): skill consolidation and long-term learning.
"""

from __future__ import annotations

import logging

from deerflow.eaib.cerebellum.skill_archiver import SkillArchiver
from deerflow.eaib.cerebellum.skill_registry import SkillRegistry, get_skill_registry
from deerflow.eaib.cerebellum.skill_types import RobotSkill, SkillStatus

logger = logging.getLogger(__name__)


class LearningPipeline:
    """Coordinates skill lifecycle transitions.

    Acts as the single integration point between:
    - Execution results (from tool calls or subagent reports)
    - SkillRegistry state machine
    - RobotMemoryStorage event log
    - SkillArchiver GC
    """

    def __init__(self, registry: SkillRegistry | None = None) -> None:
        self._registry = registry or get_skill_registry()
        self._archiver = SkillArchiver(self._registry)

    def on_skill_executed(
        self,
        skill_id: str,
        success: bool,
        stable_threshold: int = 3,
        agent_name: str | None = None,
    ) -> RobotSkill | None:
        """Called after a skill is executed.

        Promotes the skill through DRAFT → TESTED → STABLE based on success count.
        Appends an event to RobotMemoryStorage.
        """
        skill = self._registry.record_execution(
            skill_id=skill_id,
            success=success,
            stable_threshold=stable_threshold,
        )
        if skill is None:
            return None

        try:
            from deerflow.eaib.hippocampus.robot_memory_storage import RobotMemoryStorage
            from deerflow.config.paths import get_paths

            mem = RobotMemoryStorage()
            event = "skill_stable" if skill.status == SkillStatus.STABLE else ("skill_tested" if skill.status == SkillStatus.TESTED else "skill_executed")
            mem.record_skill_event(event=event, skill_id=skill_id, body_id=skill.body_id, agent_name=agent_name)
            mem.record_skill_execution(skill_id=skill_id, skill_name=skill.name, agent_name=agent_name)
        except Exception:
            logger.debug("Could not update robot memory after skill execution", exc_info=True)

        return skill

    def on_skill_created(
        self,
        name: str,
        description: str,
        body_id: str,
        code_path: str | None = None,
        tags: list[str] | None = None,
        source_thread_id: str | None = None,
        agent_name: str | None = None,
    ) -> RobotSkill:
        """Called when a new skill is authored by the Motor Cortex subagent."""
        skill = self._registry.create_skill(
            name=name,
            description=description,
            body_id=body_id,
            code_path=code_path,
            tags=tags,
            source_thread_id=source_thread_id,
        )
        try:
            from deerflow.eaib.hippocampus.robot_memory_storage import RobotMemoryStorage

            mem = RobotMemoryStorage()
            mem.record_skill_event(event="skill_created", skill_id=skill.skill_id, body_id=body_id, agent_name=agent_name)
        except Exception:
            logger.debug("Could not update robot memory after skill creation", exc_info=True)
        return skill

    def run_gc(self, body_id: str | None = None) -> list[str]:
        """Run automatic garbage collection and return archived skill IDs."""
        from deerflow.config.eaib_config import get_eaib_config

        cfg = get_eaib_config().skill_registry
        archived = self._archiver.run_garbage_collection(
            body_id=body_id,
            max_stable_skills_per_body=cfg.max_stable_skills_per_body,
        )
        return archived


# Singleton
_pipeline: LearningPipeline | None = None


def get_learning_pipeline() -> LearningPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = LearningPipeline()
    return _pipeline
