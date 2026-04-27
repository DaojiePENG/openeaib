"""Occipital-Parietal perception sub-package."""

from deerflow.eaib.occipital_parietal.camera_tool import capture_frame_tool
from deerflow.eaib.occipital_parietal.face_recognizer import FaceRecognizer, get_face_recognizer
from deerflow.eaib.occipital_parietal.sensor_reader import (
    enroll_user_face_tool,
    identify_user_face_tool,
    read_lidar_scan_tool,
    read_serial_sensor_tool,
)

PERCEPTION_TOOLS = [
    capture_frame_tool,
    read_serial_sensor_tool,
    read_lidar_scan_tool,
    identify_user_face_tool,
    enroll_user_face_tool,
]

__all__ = [
    "capture_frame_tool",
    "FaceRecognizer",
    "get_face_recognizer",
    "read_serial_sensor_tool",
    "read_lidar_scan_tool",
    "identify_user_face_tool",
    "enroll_user_face_tool",
    "PERCEPTION_TOOLS",
]
