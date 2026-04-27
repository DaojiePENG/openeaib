"""Base SDK adapter interface for robot body SDKs.

运动皮层 (Motor Cortex): abstract adapter for body-specific SDKs.
"""

from __future__ import annotations

import abc
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class ConnectionStatus:
    connected: bool
    body_id: str
    sdk_version: str | None = None
    message: str = ""


class BaseSdkAdapter(abc.ABC):
    """Abstract base class for robot SDK adapters.

    Each concrete adapter wraps a specific robot SDK (e.g. unitree_sdk2py)
    and provides a uniform interface for install, connect, and control.
    """

    @property
    @abc.abstractmethod
    def body_id(self) -> str:
        """Stable body identifier, e.g. 'unitree_g1'."""

    @property
    @abc.abstractmethod
    def sdk_package(self) -> str:
        """Pip-installable package name or GitHub URL."""

    @property
    @abc.abstractmethod
    def sdk_import_name(self) -> str:
        """Python import name to verify installation."""

    def is_installed(self) -> bool:
        """Check whether the SDK is importable."""
        import importlib.util

        return importlib.util.find_spec(self.sdk_import_name) is not None

    def install(self) -> tuple[bool, str]:
        """Attempt to install the SDK via pip.

        Returns:
            (success, message)
        """
        cmd = [sys.executable, "-m", "pip", "install", self.sdk_package]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return True, f"Installed {self.sdk_package} successfully."
            return False, f"pip install failed:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Installation timed out."
        except Exception as e:
            return False, f"Installation error: {e}"

    @abc.abstractmethod
    def connect(self, **kwargs: Any) -> ConnectionStatus:
        """Attempt to connect to the robot."""

    @abc.abstractmethod
    def get_state(self) -> dict[str, Any]:
        """Return a dict with the current robot state (joints, battery, etc.)."""

    @abc.abstractmethod
    def emergency_stop(self) -> bool:
        """Immediately halt the robot. Returns True if command was accepted."""

    def install_and_connect(self, **kwargs: Any) -> tuple[bool, str]:
        """Convenience method: install SDK if missing then connect."""
        if not self.is_installed():
            ok, msg = self.install()
            if not ok:
                return False, msg
        status = self.connect(**kwargs)
        return status.connected, status.message
