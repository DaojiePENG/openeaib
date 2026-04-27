"""EAIB robot skills management API.

Endpoints under /api/eaib/skills/ for browsing, creating, and managing robot skills.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/eaib/skills", tags=["eaib-skills"])


class SkillSummaryResponse(BaseModel):
    skill_id: str
    name: str
    description: str
    body_id: str
    status: str
    tags: list[str]
    usage_count: int
    success_count: int
    created_at: str


class SkillSearchResponse(BaseModel):
    query: str
    body_id: str
    results: list[SkillSummaryResponse]


class CreateSkillRequest(BaseModel):
    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="What this skill does")
    body_id: str = Field(..., description="Target body or 'universal'")
    code_path: str = Field("", description="Optional path to skill Python script")
    tags: list[str] = Field(default_factory=list)


@router.get("/", response_model=list[SkillSummaryResponse])
def list_skills(
    body_id: str = Query("", description="Filter by body_id; empty = use current body"),
    include_universal: bool = Query(True),
    status: str = Query("", description="Filter by status (draft/tested/stable/archived)"),
) -> list[SkillSummaryResponse]:
    """List robot skills for a given body."""
    from deerflow.eaib.body.body_registry import get_body_registry
    from deerflow.eaib.cerebellum.skill_registry import get_skill_registry

    if not body_id:
        body_id = get_body_registry().current_body_id

    registry = get_skill_registry()
    skills = registry.list_by_body(body_id, include_universal=include_universal)

    if status:
        skills = [s for s in skills if s.status.value == status]

    return [
        SkillSummaryResponse(
            skill_id=s.skill_id,
            name=s.name,
            description=s.description,
            body_id=s.body_id,
            status=s.status.value,
            tags=list(s.tags),
            usage_count=s.usage_count,
            success_count=s.success_count,
            created_at=s.created_at,
        )
        for s in skills
    ]


@router.get("/search", response_model=SkillSearchResponse)
def search_skills(
    q: str = Query(..., description="Search keywords"),
    body_id: str = Query("", description="Scope to body; empty = current body"),
    limit: int = Query(10),
) -> SkillSearchResponse:
    """Search skills by keyword."""
    from deerflow.eaib.body.body_registry import get_body_registry
    from deerflow.eaib.cerebellum.skill_registry import get_skill_registry

    if not body_id:
        body_id = get_body_registry().current_body_id

    registry = get_skill_registry()
    skills = registry.search(query=q, body_id=body_id, limit=limit)

    return SkillSearchResponse(
        query=q,
        body_id=body_id,
        results=[
            SkillSummaryResponse(
                skill_id=s.skill_id,
                name=s.name,
                description=s.description,
                body_id=s.body_id,
                status=s.status.value,
                tags=list(s.tags),
                usage_count=s.usage_count,
                success_count=s.success_count,
                created_at=s.created_at,
            )
            for s in skills
        ],
    )


@router.get("/{skill_id}", response_model=SkillSummaryResponse)
def get_skill(skill_id: str) -> SkillSummaryResponse:
    """Get a single skill by ID."""
    from deerflow.eaib.cerebellum.skill_registry import get_skill_registry

    registry = get_skill_registry()
    skill = registry.get(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
    return SkillSummaryResponse(
        skill_id=skill.skill_id,
        name=skill.name,
        description=skill.description,
        body_id=skill.body_id,
        status=skill.status.value,
        tags=list(skill.tags),
        usage_count=skill.usage_count,
        success_count=skill.success_count,
        created_at=skill.created_at,
    )


@router.post("/", status_code=201, response_model=SkillSummaryResponse)
def create_skill(req: CreateSkillRequest) -> SkillSummaryResponse:
    """Create a new robot skill."""
    from deerflow.eaib.cerebellum.skill_registry import get_skill_registry

    registry = get_skill_registry()
    skill = registry.create_skill(
        name=req.name,
        description=req.description,
        body_id=req.body_id,
        code_path=req.code_path or None,
        tags=req.tags,
    )
    return SkillSummaryResponse(
        skill_id=skill.skill_id,
        name=skill.name,
        description=skill.description,
        body_id=skill.body_id,
        status=skill.status.value,
        tags=list(skill.tags),
        usage_count=skill.usage_count,
        success_count=skill.success_count,
        created_at=skill.created_at,
    )


@router.delete("/{skill_id}", status_code=200)
def archive_skill(skill_id: str) -> dict:
    """Archive (soft-delete) a skill."""
    from deerflow.eaib.cerebellum.skill_archiver import SkillArchiver

    archiver = SkillArchiver()
    ok = archiver.archive_by_user(skill_id, reason="Archived via API")
    if not ok:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
    return {"ok": True, "skill_id": skill_id}
