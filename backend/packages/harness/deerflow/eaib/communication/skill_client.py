"""Robot-to-robot skill sharing client.

机器人间通信: HTTP client for fetching skills from peer EAIB instances.

Usage (from motor cortex agent or tool):
    client = SkillClient(base_url="http://192.168.1.42:8001/api/eaib/peer")
    skills = await client.list_skills(body_id="universal")
    detail = await client.get_skill("skill_abc")
    ok = await client.push_skill(my_skill, code="...")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0


@dataclass
class RemoteSkill:
    skill_id: str
    name: str
    description: str
    body_id: str
    status: str
    tags: list[str]
    usage_count: int
    success_count: int
    code: str | None = None


class SkillClient:
    """Async HTTP client for the EAIB peer skill sharing API."""

    def __init__(self, base_url: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    async def list_skills(self, body_id: str = "") -> list[RemoteSkill]:
        """List stable skills available on the peer robot."""
        params = {"body_id": body_id} if body_id else {}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._base}/skills", params=params)
            resp.raise_for_status()
            return [RemoteSkill(**item) for item in resp.json()]

    async def get_skill(self, skill_id: str) -> RemoteSkill:
        """Fetch full skill detail (including code) from a peer."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._base}/skills/{skill_id}")
            resp.raise_for_status()
            return RemoteSkill(**resp.json())

    async def push_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        body_id: str,
        tags: list[str],
        code: str | None = None,
        source_robot: str | None = None,
    ) -> dict:
        """Push a local skill to a peer robot's registry."""
        payload = {
            "skill_id": skill_id,
            "name": name,
            "description": description,
            "body_id": body_id,
            "tags": tags,
            "code": code,
            "source_robot": source_robot,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._base}/skills/import", json=payload)
            resp.raise_for_status()
            return resp.json()

    @classmethod
    def from_body_id(cls, peer_body_id: str, port: int = 8001) -> "SkillClient | None":
        """Try to construct a client from a peer body's known IP (if stored in registry)."""
        try:
            from deerflow.eaib.body.body_registry import get_body_registry

            registry = get_body_registry()
            profile = registry.get(peer_body_id)
            if profile is None:
                return None
            ip = profile.metadata.get("ip_address")
            if not ip:
                return None
            return cls(base_url=f"http://{ip}:{port}/api/eaib/peer")
        except Exception as exc:
            logger.warning("SkillClient.from_body_id failed: %s", exc)
            return None
