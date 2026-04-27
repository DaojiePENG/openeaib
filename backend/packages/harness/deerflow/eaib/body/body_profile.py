"""BodyProfile — robot body identity and sensor manifest.

The 岛叶皮层 (Insular Cortex) module for body self-awareness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class SensorDescriptor:
    """Descriptor for a single sensor or peripheral."""

    name: str
    """Logical name, e.g. 'front_camera', 'lidar_main', 'imu'."""
    sensor_type: str
    """One of: camera | lidar | imu | microphone | speaker | joint_encoder |
    odometer | gps | depth_camera | force_torque | gpu | cpu | ram | other."""
    device_path: str | None = None
    """OS device path, e.g. '/dev/video0'."""
    ros_topic: str | None = None
    """ROS2 topic name if sensor is ROS-managed."""
    available: bool = True
    """Whether the sensor is currently accessible."""
    extra: dict[str, Any] = field(default_factory=dict)
    """Free-form metadata (resolution, fps, baud_rate, …)."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sensor_type": self.sensor_type,
            "device_path": self.device_path,
            "ros_topic": self.ros_topic,
            "available": self.available,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SensorDescriptor":
        return cls(
            name=data["name"],
            sensor_type=data["sensor_type"],
            device_path=data.get("device_path"),
            ros_topic=data.get("ros_topic"),
            available=data.get("available", True),
            extra=data.get("extra", {}),
        )


@dataclass
class BodyProfile:
    """Complete identity profile of a robot body.

    A "body" is the physical substrate the EAIB brain is currently embodied in.
    Special body_id ``host`` represents the bare Linux control PC without any
    attached robot chassis.
    """

    body_id: str
    """Unique stable identifier, e.g. 'unitree_g1', 'unitree_go2', 'host'."""
    body_name: str
    """Human-readable display name, e.g. 'Unitree G1 Humanoid Robot'."""
    body_type: str
    """Classification: 'humanoid' | 'quadruped' | 'arm' | 'wheeled' | 'aerial' | 'host' | 'unknown'."""
    sensors: list[SensorDescriptor] = field(default_factory=list)
    """All detected or manually registered sensors for this body."""
    sdks: list[str] = field(default_factory=list)
    """Installed SDK package names, e.g. ['unitree_sdk2py', 'ros2']."""
    notes: str = ""
    """Free-text notes about this body."""
    first_seen: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_sensors_by_type(self, sensor_type: str) -> list[SensorDescriptor]:
        return [s for s in self.sensors if s.sensor_type == sensor_type]

    def has_sensor_type(self, sensor_type: str) -> bool:
        return any(s.sensor_type == sensor_type and s.available for s in self.sensors)

    def available_sensor_types(self) -> list[str]:
        return sorted({s.sensor_type for s in self.sensors if s.available})

    def touch(self) -> None:
        """Update last_seen to now."""
        self.last_seen = datetime.now(UTC).isoformat()

    def describe(self) -> str:
        """Return a concise human-readable description for prompt injection."""
        sensor_summary = ", ".join(self.available_sensor_types()) or "none"
        sdk_summary = ", ".join(self.sdks) or "none"
        return (
            f"Body: {self.body_name} (ID: {self.body_id}, type: {self.body_type})\n"
            f"Available sensors: {sensor_summary}\n"
            f"Installed SDKs: {sdk_summary}"
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "body_id": self.body_id,
            "body_name": self.body_name,
            "body_type": self.body_type,
            "sensors": [s.to_dict() for s in self.sensors],
            "sdks": self.sdks,
            "notes": self.notes,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BodyProfile":
        return cls(
            body_id=data["body_id"],
            body_name=data["body_name"],
            body_type=data.get("body_type", "unknown"),
            sensors=[SensorDescriptor.from_dict(s) for s in data.get("sensors", [])],
            sdks=data.get("sdks", []),
            notes=data.get("notes", ""),
            first_seen=data.get("first_seen", datetime.now(UTC).isoformat()),
            last_seen=data.get("last_seen", datetime.now(UTC).isoformat()),
        )


# Canonical "no hardware" profile used before any robot is attached.
HOST_BODY_PROFILE = BodyProfile(
    body_id="host",
    body_name="Linux Control Host",
    body_type="host",
    notes="Bare control computer with no robot chassis connected.",
)
