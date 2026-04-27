"""Skill management tools exposed to the EAIB agent.

These tools let the agent query, create, archive, and execute robot skills.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool("list_robot_skills")
def list_robot_skills_tool(body_id: str = "") -> str:
    """List all available robot skills for the current or specified body.

    Args:
        body_id: Body ID to filter by. Uses the current active body if empty.
                 Pass 'universal' to see only cross-body skills.

    Returns:
        JSON list of skills with id, name, body_id, status, and description.
    """
    try:
        from deerflow.eaib.cerebellum.skill_registry import get_skill_registry
        from deerflow.eaib.body.body_registry import get_body_registry

        registry = get_skill_registry()
        if not body_id:
            body_id = get_body_registry().current_body_id
        skills = registry.list_by_body(body_id, include_universal=True)
        return json.dumps({"body_id": body_id, "skills": [s.to_dict() for s in skills], "count": len(skills)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("search_robot_skills")
def search_robot_skills_tool(query: str, body_id: str = "") -> str:
    """Search for robot skills by keyword.

    Args:
        query: Space-separated keywords to match against skill name, description, and tags.
        body_id: Body ID to scope search. Uses current body if empty.

    Returns:
        JSON list of matching skills ranked by relevance.
    """
    try:
        from deerflow.eaib.cerebellum.skill_registry import get_skill_registry
        from deerflow.eaib.body.body_registry import get_body_registry

        registry = get_skill_registry()
        if not body_id:
            body_id = get_body_registry().current_body_id
        skills = registry.search(query, body_id=body_id if body_id else None)
        return json.dumps({"query": query, "results": [s.to_dict() for s in skills]}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("save_robot_skill")
def save_robot_skill_tool(
    name: str,
    description: str,
    body_id: str,
    code_path: str = "",
    tags: str = "",
) -> str:
    """Save a newly developed robot skill to the Cerebellum registry.

    Call this after successfully writing and testing a new skill script.

    Args:
        name: Human-readable skill name, e.g. 'Shake Hand'.
        description: What this skill does (1-3 sentences).
        body_id: Target body, e.g. 'unitree_g1' or 'universal'.
        code_path: Path to the skill's Python script (relative to skills_code_dir).
        tags: Comma-separated tags, e.g. 'locomotion,greeting'.

    Returns:
        JSON with the new skill's ID and status.
    """
    try:
        from deerflow.eaib.hippocampus.learning_pipeline import get_learning_pipeline

        pipeline = get_learning_pipeline()
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        skill = pipeline.on_skill_created(
            name=name,
            description=description,
            body_id=body_id,
            code_path=code_path or None,
            tags=tag_list,
        )
        return json.dumps({"skill_id": skill.skill_id, "status": skill.status.value, "name": skill.name})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("record_skill_execution")
def record_skill_execution_tool(skill_id: str, success: bool = True) -> str:
    """Record the result of a skill execution.

    Call this after running a skill to update its lifecycle status.
    On success, the skill may be promoted from DRAFT → TESTED → STABLE.

    Args:
        skill_id: The skill's ID (from save_robot_skill or list_robot_skills).
        success: Whether the execution was successful.

    Returns:
        JSON with updated skill status.
    """
    try:
        from deerflow.eaib.hippocampus.learning_pipeline import get_learning_pipeline
        from deerflow.config.eaib_config import get_eaib_config

        pipeline = get_learning_pipeline()
        threshold = get_eaib_config().skill_registry.stable_threshold
        skill = pipeline.on_skill_executed(skill_id=skill_id, success=success, stable_threshold=threshold)
        if skill is None:
            return json.dumps({"error": f"Skill '{skill_id}' not found"})
        return json.dumps({"skill_id": skill.skill_id, "status": skill.status.value, "success_count": skill.success_count})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("archive_robot_skill")
def archive_robot_skill_tool(skill_id: str, reason: str = "Archived by agent request") -> str:
    """Archive a robot skill (move it to the graveyard).

    Use this when a skill is superseded, broken, or no longer needed.

    Args:
        skill_id: The skill ID to archive.
        reason: Why the skill is being archived.

    Returns:
        JSON confirming the archival.
    """
    try:
        from deerflow.eaib.cerebellum.skill_archiver import SkillArchiver

        archiver = SkillArchiver()
        ok = archiver.archive_by_user(skill_id, reason=reason)
        return json.dumps({"archived": ok, "skill_id": skill_id, "reason": reason})
    except Exception as e:
        return json.dumps({"error": str(e)})
