"""EAIB body management API.

Endpoints under /api/eaib/body/ for managing robot body profiles.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/eaib/body", tags=["eaib-body"])


class BodySummary(BaseModel):
    body_id: str
    display_name: str
    hardware_type: str
    is_current: bool
    sensor_count: int
    sdk_packages: list[str]


class SetCurrentBodyRequest(BaseModel):
    body_id: str = Field(..., description="Body ID to activate")


class RegisterBodyRequest(BaseModel):
    body_id: str = Field(..., description="Unique body identifier, e.g. 'my_arm_v2'")
    display_name: str = Field("", description="Human-readable name")
    hardware_type: str = Field("custom", description="Hardware category (humanoid/quadruped/arm/custom/…)")
    metadata: dict = Field(default_factory=dict, description="Free-form metadata (ip_address, notes, …)")


@router.get("/", response_model=list[BodySummary])
def list_bodies() -> list[BodySummary]:
    """List all registered robot body profiles."""
    from deerflow.eaib.body.body_registry import get_body_registry

    registry = get_body_registry()
    current_id = registry.current_body_id
    return [
        BodySummary(
            body_id=p.body_id,
            display_name=p.display_name,
            hardware_type=p.hardware_type,
            is_current=(p.body_id == current_id),
            sensor_count=len(p.sensors),
            sdk_packages=list(p.sdk_packages),
        )
        for p in registry.list_all()
    ]


@router.get("/current", response_model=BodySummary)
def get_current_body() -> BodySummary:
    """Return the currently active robot body."""
    from deerflow.eaib.body.body_registry import get_body_registry

    registry = get_body_registry()
    profile = registry.get_current_body()
    if profile is None:
        raise HTTPException(status_code=404, detail="No body configured")
    return BodySummary(
        body_id=profile.body_id,
        display_name=profile.display_name,
        hardware_type=profile.hardware_type,
        is_current=True,
        sensor_count=len(profile.sensors),
        sdk_packages=list(profile.sdk_packages),
    )


@router.post("/current", status_code=200)
def set_current_body(req: SetCurrentBodyRequest) -> dict:
    """Set the active robot body."""
    from deerflow.eaib.body.body_registry import get_body_registry

    registry = get_body_registry()
    try:
        registry.set_current_body(req.body_id)
        return {"ok": True, "body_id": req.body_id}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Body '{req.body_id}' not registered")


@router.post("/register", status_code=201)
def register_body(req: RegisterBodyRequest) -> dict:
    """Register a new robot body profile."""
    from deerflow.eaib.body.body_profile import BodyProfile
    from deerflow.eaib.body.body_registry import get_body_registry

    registry = get_body_registry()
    profile = BodyProfile(
        body_id=req.body_id,
        display_name=req.display_name or req.body_id,
        hardware_type=req.hardware_type,
        metadata=req.metadata,
    )
    registry.register(profile)
    return {"ok": True, "body_id": req.body_id}


@router.get("/scan")
def scan_hardware() -> dict:
    """Scan the host OS for connected hardware peripherals."""
    from deerflow.eaib.body.hardware_scanner import get_hardware_scanner

    scanner = get_hardware_scanner()
    return scanner.scan_summary()


@router.delete("/{body_id}", status_code=200)
def delete_body(body_id: str) -> dict:
    """Remove a body profile from the registry."""
    from deerflow.eaib.body.body_registry import get_body_registry

    registry = get_body_registry()
    if registry.get(body_id) is None:
        raise HTTPException(status_code=404, detail=f"Body '{body_id}' not found")
    registry.delete(body_id)
    return {"ok": True, "body_id": body_id}
