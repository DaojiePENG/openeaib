"""Runtime-mutable SDK adapter registry.

运动皮层 (Motor Cortex): manages the set of known robot adapters.

At startup the registry is EMPTY. Adapters are discovered at runtime through
user conversation and persisted to disk by the motor cortex agent.

Storage layout:
  ~/.local/share/eaib/adapters/
    <body_id>/
      adapter.py         ← generated Python code (BaseSdkAdapter subclass)
      meta.json          ← body_id, sdk_package, created_at, notes
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deerflow.eaib.motor_cortex.sdk_adapters.base_adapter import BaseSdkAdapter

logger = logging.getLogger(__name__)


def _default_adapters_dir() -> Path:
    try:
        from deerflow.config.eaib_config import get_eaib_config

        base = Path(get_eaib_config().body_registry.storage_dir).parent
    except Exception:
        base = Path.home() / ".local" / "share" / "eaib"
    return base / "adapters"


class AdapterRegistry:
    """Thread-safe, disk-persisted registry of robot SDK adapters.

    Adapters are NOT pre-loaded. The motor cortex agent populates this registry
    by generating `adapter.py` files through conversation with the user.

    Usage by motor cortex agent:
    1. User describes robot and SDK
    2. Agent generates adapter code using `DynamicSdkAdapter.render_template()`
    3. Agent writes code to file and calls `registry.register_from_file(body_id, path)`
    4. On next startup, `registry.load_all()` auto-discovers all persisted adapters
    """

    def __init__(self, adapters_dir: Path | None = None) -> None:
        self._dir = adapters_dir or _default_adapters_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._registry: dict[str, BaseSdkAdapter] = {}

    # ------------------------------------------------------------------
    # Discovery and loading
    # ------------------------------------------------------------------

    def load_all(self) -> list[str]:
        """Scan the adapters directory and load all valid adapters.

        Returns:
            List of body_ids that were successfully loaded.
        """
        from deerflow.eaib.motor_cortex.sdk_adapters.dynamic_adapter import DynamicSdkAdapter

        loaded: list[str] = []
        for body_dir in sorted(self._dir.iterdir()):
            if not body_dir.is_dir():
                continue
            adapter_py = body_dir / "adapter.py"
            if not adapter_py.exists():
                continue
            try:
                adapter = DynamicSdkAdapter.from_file(adapter_py)
                with self._lock:
                    self._registry[adapter.body_id] = adapter
                loaded.append(adapter.body_id)
            except Exception as e:
                logger.warning("Failed to load adapter from %s: %s", adapter_py, e)
        return loaded

    def register_from_file(self, body_id: str, adapter_py_path: Path | str, notes: str = "") -> bool:
        """Load an adapter from a Python file and register it.

        Called by the motor cortex agent after generating and writing an adapter file.

        Args:
            body_id: Robot body identifier, e.g. 'my_arm_v2'.
            adapter_py_path: Path to the generated adapter.py file.
            notes: Optional free-text notes about this adapter.

        Returns:
            True if registration succeeded.
        """
        from deerflow.eaib.motor_cortex.sdk_adapters.dynamic_adapter import DynamicSdkAdapter

        src = Path(adapter_py_path)
        dest_dir = self._dir / body_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "adapter.py"

        # Copy to canonical location if provided path is elsewhere
        if src.resolve() != dest.resolve():
            import shutil
            shutil.copy2(src, dest)

        try:
            adapter = DynamicSdkAdapter.from_file(dest)
        except Exception as e:
            logger.error("Cannot register adapter for '%s': %s", body_id, e)
            return False

        meta = {
            "body_id": body_id,
            "sdk_package": adapter.sdk_package,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes,
        }
        (dest_dir / "meta.json").write_text(json.dumps(meta, indent=2))

        with self._lock:
            self._registry[adapter.body_id] = adapter

        logger.info("Registered adapter for body_id='%s'", body_id)
        return True

    def register_in_memory(self, adapter: BaseSdkAdapter) -> None:
        """Register a pre-built adapter instance (not persisted to disk).

        Useful for unit tests and examples.
        """
        with self._lock:
            self._registry[adapter.body_id] = adapter

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, body_id: str) -> BaseSdkAdapter | None:
        with self._lock:
            return self._registry.get(body_id)

    def list_all(self) -> list[dict[str, Any]]:
        """Return summary dicts for all registered adapters."""
        result = []
        for body_id, adapter in list(self._registry.items()):
            meta_path = self._dir / body_id / "meta.json"
            meta = {}
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                except Exception:
                    pass
            result.append({
                "body_id": body_id,
                "sdk_package": adapter.sdk_package,
                "installed": adapter.is_installed(),
                "notes": meta.get("notes", ""),
                "created_at": meta.get("created_at", ""),
            })
        return result

    def list_body_ids(self) -> list[str]:
        with self._lock:
            return list(self._registry.keys())

    def remove(self, body_id: str, delete_files: bool = False) -> bool:
        """Remove an adapter from the registry.

        Args:
            body_id: Body ID to remove.
            delete_files: If True, also delete the adapter.py and meta.json from disk.
        """
        with self._lock:
            if body_id not in self._registry:
                return False
            del self._registry[body_id]

        if delete_files:
            import shutil
            body_dir = self._dir / body_id
            if body_dir.exists():
                shutil.rmtree(body_dir)

        return True

    def discover_unregistered(self) -> list[str]:
        """Find body_ids that have adapter.py on disk but are not currently registered."""
        registered = set(self.list_body_ids())
        unregistered = []
        for body_dir in self._dir.iterdir():
            if not body_dir.is_dir():
                continue
            if (body_dir / "adapter.py").exists() and body_dir.name not in registered:
                unregistered.append(body_dir.name)
        return unregistered

    def get_adapter_code(self, body_id: str) -> str | None:
        """Read the raw adapter.py source for a given body_id (for inspection/editing)."""
        p = self._dir / body_id / "adapter.py"
        return p.read_text() if p.exists() else None

    def get_example_template(self, body_id: str, sdk_package: str = "UNKNOWN") -> str:
        """Generate a blank adapter template for the agent to fill in."""
        from deerflow.eaib.motor_cortex.sdk_adapters.dynamic_adapter import DynamicSdkAdapter

        sdk_import_name = sdk_package.replace("-", "_").split("@")[0].split("[")[0]
        return DynamicSdkAdapter.render_template(
            body_id=body_id,
            sdk_package=sdk_package,
            sdk_import_name=sdk_import_name,
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_registry_instance: AdapterRegistry | None = None
_registry_lock = threading.Lock()


def get_adapter_registry() -> AdapterRegistry:
    """Return the process-level AdapterRegistry singleton.

    Lazily loads all persisted adapters on first access.
    """
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                r = AdapterRegistry()
                loaded = r.load_all()
                if loaded:
                    logger.info("Loaded %d robot adapter(s): %s", len(loaded), loaded)
                else:
                    logger.debug("No persisted robot adapters found — registry is empty until user connects a robot")
                _registry_instance = r
    return _registry_instance


def reset_adapter_registry() -> None:
    """Clear the singleton (for testing only)."""
    global _registry_instance
    _registry_instance = None
