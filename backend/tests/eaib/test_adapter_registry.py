"""Tests for AdapterRegistry."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from deerflow.eaib.motor_cortex.sdk_adapters.adapter_registry import AdapterRegistry, reset_adapter_registry


MINIMAL_ADAPTER_PY = textwrap.dedent("""\
    from deerflow.eaib.motor_cortex.sdk_adapters.base_adapter import BaseSdkAdapter, ConnectionStatus

    class Adapter(BaseSdkAdapter):
        body_id = "test_body"
        sdk_package = "fake_sdk"
        sdk_import_name = "fake_sdk"

        def connect(self, **kwargs) -> ConnectionStatus:
            return ConnectionStatus(connected=True, body_id=self.body_id, message="ok")

        def get_state(self) -> dict:
            return {"battery": 100}

        def emergency_stop(self) -> bool:
            return True
""")


@pytest.fixture()
def registry(tmp_path: Path) -> AdapterRegistry:
    reset_adapter_registry()
    return AdapterRegistry(storage_dir=tmp_path / "adapters")


@pytest.fixture()
def adapter_file(tmp_path: Path) -> Path:
    p = tmp_path / "test_adapter.py"
    p.write_text(MINIMAL_ADAPTER_PY, encoding="utf-8")
    return p


def test_starts_empty(registry: AdapterRegistry) -> None:
    assert registry.list_all() == []


def test_register_from_file(registry: AdapterRegistry, adapter_file: Path) -> None:
    registry.register_from_file(body_id="test_body", path=adapter_file, notes="test")
    assert registry.get("test_body") is not None


def test_list_all_after_register(registry: AdapterRegistry, adapter_file: Path) -> None:
    registry.register_from_file(body_id="test_body", path=adapter_file)
    entries = registry.list_all()
    assert len(entries) == 1
    assert entries[0]["body_id"] == "test_body"


def test_remove_adapter(registry: AdapterRegistry, adapter_file: Path) -> None:
    registry.register_from_file(body_id="test_body", path=adapter_file)
    registry.remove("test_body")
    assert registry.get("test_body") is None


def test_get_example_template() -> None:
    registry = AdapterRegistry.__new__(AdapterRegistry)
    registry._storage_dir = Path("/tmp/fake")
    registry._adapters = {}
    registry._lock = __import__("threading").Lock()
    template = registry.get_example_template(body_id="my_robot", sdk_package="my_sdk")
    assert "my_robot" in template
    assert "my_sdk" in template or "Adapter" in template
