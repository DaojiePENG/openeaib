"""Robot-to-robot communication sub-package."""

from deerflow.eaib.communication.skill_client import RemoteSkill, SkillClient
from deerflow.eaib.communication.skill_server import skill_server_app

__all__ = [
    "skill_server_app",
    "SkillClient",
    "RemoteSkill",
]
