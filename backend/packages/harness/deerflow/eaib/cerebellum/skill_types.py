"""RobotSkill — data model for robot skills stored in the Cerebellum registry.

小脑 (Cerebellum): skill identity and lifecycle types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class SkillStatus(str, Enum):
    """Lifecycle stages of a robot skill."""

    DRAFT = "draft"
    """Generated but not yet executed successfully."""
    TESTED = "tested"
    """Executed successfully at least once."""
    STABLE = "stable"
    """Executed successfully N times (stable_threshold), ready for production use."""
    ARCHIVED = "archived"
    """Moved to archive: superseded, broken, or explicitly retired."""


@dataclass
class RobotSkill:
    """A single executable robot skill with full provenance metadata."""

    skill_id: str
    """Unique identifier, e.g. 'shake_hand_g1_v1'."""
    name: str
    """Human-readable name, e.g. 'Shake Hand'."""
    description: str
    """One-paragraph description of what the skill does."""
    body_id: str
    """Target body ID: 'universal' for cross-body skills, or specific ID like 'unitree_g1'."""
    status: SkillStatus = SkillStatus.DRAFT
    code_path: str | None = None
    """Relative path to the skill's Python script under the skills_code_dir."""
    entry_point: str = "run"
    """Function name to call as the skill entry point."""
    dependencies: list[str] = field(default_factory=list)
    """Python package names required (pip-installable)."""
    tags: list[str] = field(default_factory=list)
    """Free-form tags for retrieval, e.g. ['locomotion', 'greeting', 'manipulation']."""
    usage_count: int = 0
    """Number of successful executions."""
    success_count: int = 0
    """Successful executions (subset of usage_count)."""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    tested_at: str | None = None
    stable_at: str | None = None
    archived_at: str | None = None
    archive_reason: str | None = None
    version: int = 1
    superseded_by: str | None = None
    """skill_id of the newer skill that replaced this one."""
    source_thread_id: str | None = None
    """LangGraph thread ID in which the skill was developed."""

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    def mark_tested(self) -> None:
        self.status = SkillStatus.TESTED
        self.tested_at = datetime.now(UTC).isoformat()
        self.success_count += 1
        self.usage_count += 1

    def mark_stable(self) -> None:
        self.status = SkillStatus.STABLE
        self.stable_at = datetime.now(UTC).isoformat()

    def record_execution(self, success: bool = True) -> None:
        self.usage_count += 1
        if success:
            self.success_count += 1

    def archive(self, reason: str, superseded_by: str | None = None) -> None:
        self.status = SkillStatus.ARCHIVED
        self.archived_at = datetime.now(UTC).isoformat()
        self.archive_reason = reason
        self.superseded_by = superseded_by

    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "body_id": self.body_id,
            "status": self.status.value,
            "code_path": self.code_path,
            "entry_point": self.entry_point,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "created_at": self.created_at,
            "tested_at": self.tested_at,
            "stable_at": self.stable_at,
            "archived_at": self.archived_at,
            "archive_reason": self.archive_reason,
            "version": self.version,
            "superseded_by": self.superseded_by,
            "source_thread_id": self.source_thread_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RobotSkill":
        skill = cls(
            skill_id=data["skill_id"],
            name=data["name"],
            description=data["description"],
            body_id=data["body_id"],
            status=SkillStatus(data.get("status", SkillStatus.DRAFT.value)),
            code_path=data.get("code_path"),
            entry_point=data.get("entry_point", "run"),
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
            tested_at=data.get("tested_at"),
            stable_at=data.get("stable_at"),
            archived_at=data.get("archived_at"),
            archive_reason=data.get("archive_reason"),
            version=data.get("version", 1),
            superseded_by=data.get("superseded_by"),
            source_thread_id=data.get("source_thread_id"),
        )
        return skill

    def one_line(self) -> str:
        """Compact string for prompt injection."""
        return f"[{self.skill_id}] {self.name} ({self.body_id}, {self.status.value}): {self.description[:80]}"
