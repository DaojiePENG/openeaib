"""RobotMemoryStorage — extends FileMemoryStorage with EAIB robot fields.

海马体 (Hippocampus): long-term memory with robot body and skill awareness.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deerflow.agents.memory.storage import FileMemoryStorage, create_empty_memory

logger = logging.getLogger(__name__)


def _empty_robot_memory() -> dict[str, Any]:
    """Return the robot-specific extension block."""
    return {
        "currentBody": {
            "body_id": "host",
            "body_name": "Linux Control Host",
            "body_type": "host",
            "set_at": "",
        },
        "knownBodies": {},
        "skillStats": {},
        "learningEvents": [],
    }


class RobotMemoryStorage(FileMemoryStorage):
    """Extends FileMemoryStorage to persist robot body and skill metadata.

    The memory JSON structure gains a top-level ``robot`` key:
    {
      ...(standard DeerFlow memory fields)...
      "robot": {
        "currentBody": { body_id, body_name, body_type, set_at },
        "knownBodies": { "<body_id>": { profile_snapshot, first_seen, total_skills } },
        "skillStats": { "<skill_id>": { name, executions, last_used } },
        "learningEvents": [ { event, skill_id, body_id, ts } ]  (last 50)
      }
    }
    """

    def load(self, agent_name: str | None = None) -> dict[str, Any]:
        data = super().load(agent_name)
        if "robot" not in data:
            data["robot"] = _empty_robot_memory()
        return data

    def reload(self, agent_name: str | None = None) -> dict[str, Any]:
        data = super().reload(agent_name)
        if "robot" not in data:
            data["robot"] = _empty_robot_memory()
        return data

    # ------------------------------------------------------------------
    # Robot-specific helpers
    # ------------------------------------------------------------------

    def update_current_body(self, body_id: str, body_name: str, body_type: str, agent_name: str | None = None) -> None:
        """Record the currently active body in memory."""
        data = self.load(agent_name)
        robot = data.setdefault("robot", _empty_robot_memory())
        robot["currentBody"] = {
            "body_id": body_id,
            "body_name": body_name,
            "body_type": body_type,
            "set_at": datetime.now(UTC).isoformat(),
        }
        # Track in known bodies
        if body_id not in robot["knownBodies"]:
            robot["knownBodies"][body_id] = {
                "body_name": body_name,
                "body_type": body_type,
                "first_seen": datetime.now(UTC).isoformat(),
                "total_skills": 0,
            }
        self.save(data, agent_name)

    def record_skill_event(
        self,
        event: str,
        skill_id: str,
        body_id: str,
        agent_name: str | None = None,
    ) -> None:
        """Append a skill lifecycle event (created / tested / stable / archived)."""
        data = self.load(agent_name)
        robot = data.setdefault("robot", _empty_robot_memory())
        events: list[dict] = robot.setdefault("learningEvents", [])
        events.append({
            "event": event,
            "skill_id": skill_id,
            "body_id": body_id,
            "ts": datetime.now(UTC).isoformat(),
        })
        # Keep only the last 100 events
        robot["learningEvents"] = events[-100:]
        self.save(data, agent_name)

    def record_skill_execution(
        self,
        skill_id: str,
        skill_name: str,
        agent_name: str | None = None,
    ) -> None:
        """Update skill execution stats in memory."""
        data = self.load(agent_name)
        robot = data.setdefault("robot", _empty_robot_memory())
        stats: dict = robot.setdefault("skillStats", {})
        entry = stats.setdefault(skill_id, {"name": skill_name, "executions": 0, "last_used": ""})
        entry["executions"] += 1
        entry["last_used"] = datetime.now(UTC).isoformat()
        self.save(data, agent_name)

    def get_robot_context(self, agent_name: str | None = None) -> dict[str, Any]:
        """Return the robot memory block only."""
        data = self.load(agent_name)
        return data.get("robot", _empty_robot_memory())
