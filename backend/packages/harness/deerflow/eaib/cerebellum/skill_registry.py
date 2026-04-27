"""SkillRegistry — persistent CRUD store for robot skills.

小脑 (Cerebellum): skill storage, retrieval, and lifecycle management.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deerflow.eaib.cerebellum.skill_types import RobotSkill, SkillStatus

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Thread-safe JSON-backed registry for robot skills."""

    _SCHEMA_VERSION = "1.0"

    def __init__(self, storage_path: Path) -> None:
        self._path = storage_path
        self._lock = threading.Lock()
        self._data: dict[str, Any] = self._load_or_init()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_or_init(self) -> dict[str, Any]:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except Exception:
                logger.warning("Failed to load skill registry from %s; initialising fresh.", self._path)
        return {"version": self._SCHEMA_VERSION, "skills": {}, "updated_at": datetime.now(UTC).isoformat()}

    def _persist(self) -> None:
        self._data["updated_at"] = datetime.now(UTC).isoformat()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save(self, skill: RobotSkill) -> None:
        with self._lock:
            self._data["skills"][skill.skill_id] = skill.to_dict()
            self._persist()
            logger.debug("Skill saved: %s (%s)", skill.skill_id, skill.status.value)

    def get(self, skill_id: str) -> RobotSkill | None:
        with self._lock:
            raw = self._data["skills"].get(skill_id)
            return RobotSkill.from_dict(raw) if raw else None

    def delete(self, skill_id: str) -> bool:
        with self._lock:
            if skill_id not in self._data["skills"]:
                return False
            del self._data["skills"][skill_id]
            self._persist()
            return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_all(self, include_archived: bool = False) -> list[RobotSkill]:
        with self._lock:
            skills = [RobotSkill.from_dict(v) for v in self._data["skills"].values()]
        if not include_archived:
            skills = [s for s in skills if s.status != SkillStatus.ARCHIVED]
        return sorted(skills, key=lambda s: s.created_at, reverse=True)

    def list_by_body(self, body_id: str, include_universal: bool = True, include_archived: bool = False) -> list[RobotSkill]:
        """Return skills matching the given body_id (and universal skills if requested)."""
        skills = self.list_all(include_archived=include_archived)
        result = []
        for s in skills:
            if s.body_id == body_id:
                result.append(s)
            elif include_universal and s.body_id == "universal":
                result.append(s)
        return result

    def list_stable(self, body_id: str | None = None) -> list[RobotSkill]:
        """Return only STABLE skills, optionally filtered by body."""
        if body_id:
            skills = self.list_by_body(body_id, include_universal=True)
        else:
            skills = self.list_all()
        return [s for s in skills if s.status == SkillStatus.STABLE]

    def search(self, query: str, body_id: str | None = None, limit: int = 10) -> list[RobotSkill]:
        """Simple keyword search over name, description, and tags.

        Args:
            query: Space-separated keywords.
            body_id: If set, restrict to this body + universal.
            limit: Maximum results.

        Returns:
            Ranked list of matching skills.
        """
        if body_id:
            candidates = self.list_by_body(body_id, include_universal=True)
        else:
            candidates = self.list_all()

        keywords = query.lower().split()
        scored: list[tuple[int, RobotSkill]] = []
        for skill in candidates:
            score = 0
            text = f"{skill.name} {skill.description} {' '.join(skill.tags)}".lower()
            for kw in keywords:
                if kw in skill.name.lower():
                    score += 3
                elif kw in " ".join(skill.tags).lower():
                    score += 2
                elif kw in skill.description.lower():
                    score += 1
            # Prefer stable skills
            if skill.status == SkillStatus.STABLE:
                score += 1
            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    def create_skill(
        self,
        name: str,
        description: str,
        body_id: str,
        code_path: str | None = None,
        tags: list[str] | None = None,
        source_thread_id: str | None = None,
    ) -> RobotSkill:
        """Create a new DRAFT skill and persist it."""
        skill_id = f"{body_id}_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}"
        skill = RobotSkill(
            skill_id=skill_id,
            name=name,
            description=description,
            body_id=body_id,
            code_path=code_path,
            tags=tags or [],
            source_thread_id=source_thread_id,
        )
        self.save(skill)
        return skill

    def record_execution(self, skill_id: str, success: bool = True, stable_threshold: int = 3) -> RobotSkill | None:
        """Record an execution result and potentially promote the skill."""
        skill = self.get(skill_id)
        if skill is None:
            return None
        if skill.status == SkillStatus.ARCHIVED:
            return skill

        skill.record_execution(success=success)

        if skill.status == SkillStatus.DRAFT and success:
            skill.mark_tested()
        elif skill.status == SkillStatus.TESTED and skill.success_count >= stable_threshold:
            skill.mark_stable()
            logger.info("Skill promoted to STABLE: %s", skill_id)

        self.save(skill)
        return skill

    def archive_skill(self, skill_id: str, reason: str, superseded_by: str | None = None) -> bool:
        skill = self.get(skill_id)
        if skill is None:
            return False
        skill.archive(reason=reason, superseded_by=superseded_by)
        self.save(skill)
        logger.info("Skill archived: %s (reason=%s)", skill_id, reason)
        return True

    def summary_for_prompt(self, body_id: str, max_skills: int = 20) -> str:
        """Return a compact skill listing for injection into the agent system prompt."""
        skills = self.list_by_body(body_id, include_universal=True)
        stable = [s for s in skills if s.status == SkillStatus.STABLE]
        tested = [s for s in skills if s.status == SkillStatus.TESTED]

        lines = []
        if stable:
            lines.append("**Stable skills** (ready to use):")
            for s in stable[:max_skills]:
                lines.append(f"  - {s.one_line()}")
        if tested and len(stable) < max_skills:
            lines.append("**Tested skills** (functional, not yet fully validated):")
            for s in tested[: max_skills - len(stable)]:
                lines.append(f"  - {s.one_line()}")
        if not lines:
            lines.append("No skills available yet for this body.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_registry: SkillRegistry | None = None
_registry_lock = threading.Lock()


def get_skill_registry() -> SkillRegistry:
    global _registry
    if _registry is not None:
        return _registry
    with _registry_lock:
        if _registry is None:
            from deerflow.config.eaib_config import get_eaib_config

            path = get_eaib_config().resolve_skill_registry_path()
            cfg = get_eaib_config().skill_registry
            _registry = SkillRegistry(path)
    return _registry


def reset_skill_registry() -> None:
    global _registry
    with _registry_lock:
        _registry = None
