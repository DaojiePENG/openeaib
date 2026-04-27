"""Body sub-package exports."""

from deerflow.eaib.body.body_profile import (
    HOST_BODY_PROFILE,
    BodyProfile,
    SensorDescriptor,
)
from deerflow.eaib.body.body_registry import BodyRegistry, get_body_registry
from deerflow.eaib.body.hardware_scanner import HardwareScanner, get_hardware_scanner

__all__ = [
    "BodyProfile",
    "SensorDescriptor",
    "HOST_BODY_PROFILE",
    "BodyRegistry",
    "get_body_registry",
    "HardwareScanner",
    "get_hardware_scanner",
]
