"""Tests for BodyRegistry."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from deerflow.eaib.body.body_profile import BodyProfile
from deerflow.eaib.body.body_registry import BodyRegistry, reset_body_registry


@pytest.fixture()
def registry(tmp_path: Path) -> BodyRegistry:
    reset_body_registry()
    return BodyRegistry(storage_path=tmp_path / "bodies.json")


def test_default_host_body(registry: BodyRegistry) -> None:
    bodies = registry.list_all()
    ids = [b.body_id for b in bodies]
    assert "host" in ids


def test_current_body_is_host_by_default(registry: BodyRegistry) -> None:
    assert registry.current_body_id == "host"


def test_register_and_get(registry: BodyRegistry) -> None:
    profile = BodyProfile(body_id="arm_v1", display_name="My Arm", hardware_type="arm")
    registry.register(profile)
    result = registry.get("arm_v1")
    assert result is not None
    assert result.body_id == "arm_v1"
    assert result.display_name == "My Arm"


def test_set_current(registry: BodyRegistry) -> None:
    profile = BodyProfile(body_id="go2", display_name="Go2", hardware_type="quadruped")
    registry.register(profile)
    registry.set_current_body("go2")
    assert registry.current_body_id == "go2"


def test_set_current_unknown_raises(registry: BodyRegistry) -> None:
    with pytest.raises(KeyError):
        registry.set_current_body("nonexistent")


def test_delete_body(registry: BodyRegistry) -> None:
    profile = BodyProfile(body_id="to_delete", display_name="Delete Me", hardware_type="custom")
    registry.register(profile)
    assert registry.get("to_delete") is not None
    registry.delete("to_delete")
    assert registry.get("to_delete") is None


def test_cannot_delete_host(registry: BodyRegistry) -> None:
    with pytest.raises(ValueError, match="host"):
        registry.delete("host")


def test_cannot_delete_current_body(registry: BodyRegistry) -> None:
    profile = BodyProfile(body_id="active", display_name="Active", hardware_type="custom")
    registry.register(profile)
    registry.set_current_body("active")
    with pytest.raises(ValueError, match="active"):
        registry.delete("active")


def test_persistence(tmp_path: Path) -> None:
    path = tmp_path / "bodies.json"
    reg1 = BodyRegistry(storage_path=path)
    reg1.register(BodyProfile(body_id="persistent", display_name="P", hardware_type="custom"))
    reg2 = BodyRegistry(storage_path=path)
    assert reg2.get("persistent") is not None
