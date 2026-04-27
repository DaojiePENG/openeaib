"""Tests for SkillRegistry (Cerebellum)."""
from __future__ import annotations

import pytest
from pathlib import Path

from deerflow.eaib.cerebellum.skill_registry import SkillRegistry, reset_skill_registry
from deerflow.eaib.cerebellum.skill_types import SkillStatus


@pytest.fixture()
def registry(tmp_path: Path) -> SkillRegistry:
    reset_skill_registry()
    return SkillRegistry(storage_path=tmp_path / "skills.json")


def test_create_skill(registry: SkillRegistry) -> None:
    skill = registry.create_skill(
        name="test_walk",
        description="Make robot walk forward",
        body_id="go2",
        tags=["locomotion"],
    )
    assert skill.name == "test_walk"
    assert skill.body_id == "go2"
    assert skill.status == SkillStatus.DRAFT


def test_get_skill(registry: SkillRegistry) -> None:
    skill = registry.create_skill(name="s1", description="desc", body_id="host")
    result = registry.get(skill.skill_id)
    assert result is not None
    assert result.name == "s1"


def test_list_by_body(registry: SkillRegistry) -> None:
    registry.create_skill(name="s_go2", description="d", body_id="go2")
    registry.create_skill(name="s_host", description="d", body_id="host")
    registry.create_skill(name="s_universal", description="d", body_id="universal")

    go2_skills = registry.list_by_body("go2", include_universal=False)
    ids = [s.name for s in go2_skills]
    assert "s_go2" in ids
    assert "s_host" not in ids

    go2_with_uni = registry.list_by_body("go2", include_universal=True)
    uni_names = [s.name for s in go2_with_uni]
    assert "s_universal" in uni_names


def test_record_execution_and_promote(registry: SkillRegistry) -> None:
    threshold = 3
    skill = registry.create_skill(name="promo", description="d", body_id="host")
    for _ in range(threshold):
        registry.record_execution(skill.skill_id, success=True)
    updated = registry.get(skill.skill_id)
    # After 3 successes skill should be at least TESTED
    assert updated.status in (SkillStatus.TESTED, SkillStatus.STABLE)
    assert updated.success_count == threshold


def test_search(registry: SkillRegistry) -> None:
    registry.create_skill(name="wave hand", description="Robot waves its arm", body_id="host", tags=["gesture"])
    results = registry.search(query="wave", body_id="host")
    assert any("wave" in s.name.lower() or "wave" in s.description.lower() for s in results)


def test_persistence(tmp_path: Path) -> None:
    path = tmp_path / "skills.json"
    r1 = SkillRegistry(storage_path=path)
    skill = r1.create_skill(name="persistent_skill", description="d", body_id="host")
    r2 = SkillRegistry(storage_path=path)
    assert r2.get(skill.skill_id) is not None
