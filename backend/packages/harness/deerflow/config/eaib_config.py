"""EAIBConfig — Pydantic configuration model for the EAIB subsystem.

Loaded from the ``eaib:`` section of config.yaml.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class BodyRegistryConfig(BaseModel):
    """Configuration for the body (robot identity) registry."""

    storage_path: str = Field(
        default="",
        description="Absolute path to body_registry.json. Defaults to ~/.local/share/eaib/body_registry.json.",
    )
    auto_scan_on_startup: bool = Field(
        default=True,
        description="Run hardware scan automatically when the agent starts.",
    )


class SkillRegistryConfig(BaseModel):
    """Configuration for the robot skill registry."""

    storage_path: str = Field(
        default="",
        description="Absolute path to skill_registry.json. Defaults to ~/.local/share/eaib/skill_registry.json.",
    )
    skills_code_dir: str = Field(
        default="",
        description="Directory to store generated skill code. Defaults to ~/.local/share/eaib/skills/.",
    )
    stable_threshold: int = Field(
        default=3,
        description="Number of successful executions to promote a skill from 'tested' to 'stable'.",
    )
    max_stable_skills_per_body: int = Field(
        default=200,
        description="Maximum stable skills per body_id before triggering auto-archival of duplicates.",
    )


class SafetyConfig(BaseModel):
    """Configuration for the Amygdala safety system."""

    enabled: bool = Field(
        default=True,
        description="Enable safety constraint middleware.",
    )
    block_on_high_risk: bool = Field(
        default=True,
        description="Block HIGH-risk actions entirely (requires explicit override).",
    )
    clarify_on_medium_risk: bool = Field(
        default=True,
        description="Trigger ask_clarification for MEDIUM-risk actions.",
    )
    obstacle_margin_m: float = Field(
        default=0.5,
        description="Safety margin in metres. Actions moving robot within this margin of a known obstacle are flagged.",
    )


class PerceptionConfig(BaseModel):
    """Configuration for the Parietal & Occipital perception subsystem."""

    face_recognition_enabled: bool = Field(
        default=False,
        description="Enable face recognition (opt-in, privacy-sensitive). Requires face_recognition package.",
    )
    face_db_path: str = Field(
        default="",
        description="Path to face encoding database. Defaults to ~/.local/share/eaib/faces.json.",
    )
    default_camera_device: int = Field(
        default=0,
        description="Default OpenCV camera device index.",
    )


class PeerSharingConfig(BaseModel):
    """Configuration for robot-to-robot skill sharing."""

    enabled: bool = Field(
        default=False,
        description="Enable skill sharing server.",
    )
    host: str = Field(
        default="0.0.0.0",
        description="Bind address for skill sharing server.",
    )
    port: int = Field(
        default=7890,
        description="Port for skill sharing server.",
    )
    trusted_peers: list[str] = Field(
        default_factory=list,
        description="List of trusted peer addresses (host:port) for automatic skill pull.",
    )


class EAIBConfig(BaseModel):
    """Top-level configuration for the Embodied AI Brain subsystem."""

    enabled: bool = Field(
        default=True,
        description="Enable EAIB extension. When False, falls back to standard DeerFlow lead_agent.",
    )
    body_registry: BodyRegistryConfig = Field(
        default_factory=BodyRegistryConfig,
        description="Body/robot identity registry configuration.",
    )
    skill_registry: SkillRegistryConfig = Field(
        default_factory=SkillRegistryConfig,
        description="Robot skill registry configuration.",
    )
    safety: SafetyConfig = Field(
        default_factory=SafetyConfig,
        description="Amygdala safety system configuration.",
    )
    perception: PerceptionConfig = Field(
        default_factory=PerceptionConfig,
        description="Perception subsystem configuration.",
    )
    peer_sharing: PeerSharingConfig = Field(
        default_factory=PeerSharingConfig,
        description="Robot-to-robot skill sharing configuration.",
    )

    def resolve_body_registry_path(self) -> Path:
        if self.body_registry.storage_path:
            return Path(self.body_registry.storage_path)
        return Path.home() / ".local" / "share" / "eaib" / "body_registry.json"

    def resolve_skill_registry_path(self) -> Path:
        if self.skill_registry.storage_path:
            return Path(self.skill_registry.storage_path)
        return Path.home() / ".local" / "share" / "eaib" / "skill_registry.json"

    def resolve_skills_code_dir(self) -> Path:
        if self.skill_registry.skills_code_dir:
            return Path(self.skill_registry.skills_code_dir)
        return Path.home() / ".local" / "share" / "eaib" / "skills"

    def resolve_face_db_path(self) -> Path:
        if self.perception.face_db_path:
            return Path(self.perception.face_db_path)
        return Path.home() / ".local" / "share" / "eaib" / "faces.json"


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_eaib_config: EAIBConfig | None = None


def get_eaib_config() -> EAIBConfig:
    """Return the global EAIBConfig instance.

    Falls back to defaults when EAIB section is absent from config.yaml.
    Reads from the DeerFlow AppConfig's extra fields if present.
    """
    global _eaib_config
    if _eaib_config is not None:
        return _eaib_config

    try:
        from deerflow.config.app_config import get_app_config

        app_config = get_app_config()
        raw = app_config.model_extra.get("eaib", {}) if app_config.model_extra else {}
        _eaib_config = EAIBConfig.model_validate(raw) if raw else EAIBConfig()
    except Exception:
        _eaib_config = EAIBConfig()

    return _eaib_config


def reset_eaib_config() -> None:
    """Reset the cached EAIBConfig (used in tests)."""
    global _eaib_config
    _eaib_config = None
