"""Robot-to-robot skill sharing server.

机器人间通信: FastAPI sub-app that exposes stable skills for peer robots to download.

Mount point (registered in gateway app.py):
  /api/eaib/peer/

Endpoints:
  GET  /api/eaib/peer/skills               → list stable skills for download
  GET  /api/eaib/peer/skills/{skill_id}    → get skill detail + code
  POST /api/eaib/peer/skills/import        → accept a skill pushed from another robot
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from deerflow.eaib.cerebellum.skill_registry import get_skill_registry
from deerflow.eaib.cerebellum.skill_types import SkillStatus

logger = logging.getLogger(__name__)

skill_server_app = FastAPI(title="EAIB Skill Sharing Server", docs_url=None, redoc_url=None)


class SkillSummary(BaseModel):
    skill_id: str
    name: str
    description: str
    body_id: str
    status: str
    tags: list[str]
    usage_count: int
    success_count: int


class SkillDetail(SkillSummary):
    code: str | None = None


class ImportSkillRequest(BaseModel):
    skill_id: str
    name: str
    description: str
    body_id: str
    tags: list[str] = []
    code: str | None = None
    source_robot: str | None = None


@skill_server_app.get("/skills", response_model=list[SkillSummary])
def list_shareable_skills(body_id: str = "") -> list[SkillSummary]:
    """List all STABLE skills available for download by peer robots."""
    registry = get_skill_registry()
    skills = registry.list_stable()
    if body_id:
        skills = [s for s in skills if s.body_id in (body_id, "universal")]
    return [
        SkillSummary(
            skill_id=s.skill_id,
            name=s.name,
            description=s.description,
            body_id=s.body_id,
            status=s.status.value,
            tags=list(s.tags),
            usage_count=s.usage_count,
            success_count=s.success_count,
        )
        for s in skills
    ]


@skill_server_app.get("/skills/{skill_id}", response_model=SkillDetail)
def get_skill_detail(skill_id: str) -> SkillDetail:
    """Return full skill detail including code for a given skill_id."""
    registry = get_skill_registry()
    skill = registry.get(skill_id)
    if skill is None or skill.status not in (SkillStatus.STABLE, SkillStatus.TESTED):
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found or not shareable")

    code: str | None = None
    if skill.code_path:
        p = Path(skill.code_path)
        if p.exists():
            code = p.read_text()

    return SkillDetail(
        skill_id=skill.skill_id,
        name=skill.name,
        description=skill.description,
        body_id=skill.body_id,
        status=skill.status.value,
        tags=list(skill.tags),
        usage_count=skill.usage_count,
        success_count=skill.success_count,
        code=code,
    )


@skill_server_app.post("/skills/import", status_code=201)
def import_skill(req: ImportSkillRequest) -> dict:
    """Accept a skill shared by a peer robot and add it to the local registry as DRAFT."""
    registry = get_skill_registry()

    code_path: str | None = None
    if req.code:
        from deerflow.config.eaib_config import get_eaib_config

        skills_dir = Path(get_eaib_config().resolve_skills_code_dir())
        dest_dir = skills_dir / req.body_id / "peer_imports"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{req.skill_id}.py"
        dest.write_text(req.code)
        code_path = str(dest)

    skill = registry.create_skill(
        name=req.name,
        description=f"[Imported from {req.source_robot or 'peer'}] {req.description}",
        body_id=req.body_id,
        code_path=code_path,
        tags=req.tags + ["peer_import"],
    )
    logger.info("Imported skill '%s' from peer robot '%s'", req.name, req.source_robot)
    return {"skill_id": skill.skill_id, "status": skill.status.value}
