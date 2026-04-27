"""BodyRegistry — JSON-persisted CRUD store for robot body profiles.

岛叶皮层 (Insular Cortex): body self-awareness registry.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deerflow.eaib.body.body_profile import HOST_BODY_PROFILE, BodyProfile

logger = logging.getLogger(__name__)


class BodyRegistry:
    """Thread-safe registry for known robot body profiles.

    Persists to a JSON file at the configured path. All mutations are
    written synchronously to ensure durability.
    """

    _SCHEMA_VERSION = "1.0"

    def __init__(self, storage_path: Path) -> None:
        self._path = storage_path
        self._lock = threading.Lock()
        self._data: dict[str, Any] = self._load_or_init()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_or_init(self) -> dict[str, Any]:
        if self._path.exists():
            try:
                raw = self._path.read_text(encoding="utf-8")
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data
            except Exception:
                logger.warning("Failed to load body registry from %s; initialising fresh.", self._path)
        return self._empty_store()

    def _empty_store(self) -> dict[str, Any]:
        host = HOST_BODY_PROFILE.to_dict()
        return {
            "version": self._SCHEMA_VERSION,
            "current_body_id": "host",
            "bodies": {"host": host},
            "updated_at": datetime.now(UTC).isoformat(),
        }

    def _persist(self) -> None:
        self._data["updated_at"] = datetime.now(UTC).isoformat()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def current_body_id(self) -> str:
        with self._lock:
            return self._data.get("current_body_id", "host")

    def get_current_body(self) -> BodyProfile:
        with self._lock:
            bid = self._data.get("current_body_id", "host")
            raw = self._data["bodies"].get(bid)
            if raw is None:
                return HOST_BODY_PROFILE
            return BodyProfile.from_dict(raw)

    def set_current_body(self, body_id: str) -> None:
        """Switch the active body. The body must already be registered."""
        with self._lock:
            if body_id not in self._data["bodies"]:
                raise KeyError(f"Body '{body_id}' not found in registry. Register it first.")
            prev = self._data.get("current_body_id")
            if prev and prev in self._data["bodies"]:
                # Touch last_seen on the previous body
                self._data["bodies"][prev]["last_seen"] = datetime.now(UTC).isoformat()
            self._data["current_body_id"] = body_id
            self._data["bodies"][body_id]["last_seen"] = datetime.now(UTC).isoformat()
            self._persist()
            logger.info("Active body switched: %s → %s", prev, body_id)

    def register(self, profile: BodyProfile, set_current: bool = False) -> None:
        """Register or update a body profile."""
        with self._lock:
            profile.touch()
            self._data["bodies"][profile.body_id] = profile.to_dict()
            if set_current:
                self._data["current_body_id"] = profile.body_id
            self._persist()
            logger.info("Registered body: %s (set_current=%s)", profile.body_id, set_current)

    def get(self, body_id: str) -> BodyProfile | None:
        with self._lock:
            raw = self._data["bodies"].get(body_id)
            return BodyProfile.from_dict(raw) if raw else None

    def list_all(self) -> list[BodyProfile]:
        with self._lock:
            return [BodyProfile.from_dict(v) for v in self._data["bodies"].values()]

    def delete(self, body_id: str) -> bool:
        """Remove a body profile. Cannot remove 'host' or the currently active body."""
        with self._lock:
            if body_id == "host":
                raise ValueError("Cannot delete the built-in 'host' body.")
            if body_id == self._data.get("current_body_id"):
                raise ValueError(f"Cannot delete the currently active body '{body_id}'. Switch first.")
            if body_id not in self._data["bodies"]:
                return False
            del self._data["bodies"][body_id]
            self._persist()
            return True

    def update_sensors(self, body_id: str, sensors: list[dict[str, Any]]) -> None:
        """Replace the sensor list for a registered body."""
        with self._lock:
            if body_id not in self._data["bodies"]:
                raise KeyError(f"Body '{body_id}' not registered.")
            self._data["bodies"][body_id]["sensors"] = sensors
            self._data["bodies"][body_id]["last_seen"] = datetime.now(UTC).isoformat()
            self._persist()

    def add_sdk(self, body_id: str, sdk_name: str) -> None:
        """Record that an SDK has been installed for a body."""
        with self._lock:
            if body_id not in self._data["bodies"]:
                raise KeyError(f"Body '{body_id}' not registered.")
            sdks: list[str] = self._data["bodies"][body_id].setdefault("sdks", [])
            if sdk_name not in sdks:
                sdks.append(sdk_name)
                self._persist()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_registry: BodyRegistry | None = None
_registry_lock = threading.Lock()


def get_body_registry() -> BodyRegistry:
    """Return the global BodyRegistry instance (lazy-init)."""
    global _registry
    if _registry is not None:
        return _registry
    with _registry_lock:
        if _registry is None:
            from deerflow.config.eaib_config import get_eaib_config

            path = get_eaib_config().resolve_body_registry_path()
            _registry = BodyRegistry(path)
    return _registry


def reset_body_registry() -> None:
    """Reset the singleton (used in tests)."""
    global _registry
    with _registry_lock:
        _registry = None
