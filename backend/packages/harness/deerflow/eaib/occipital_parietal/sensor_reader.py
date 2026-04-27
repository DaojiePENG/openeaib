"""Generic sensor reader tool for the Occipital-Parietal system.

顶叶&枕叶 (Parietal & Occipital Lobes): read from miscellaneous sensors
not covered by the Motor Cortex ROS2 tools (e.g. USB HID, serial, I2C).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool("read_serial_sensor")
def read_serial_sensor_tool(
    port: str = "/dev/ttyUSB0",
    baudrate: int = 115200,
    num_lines: int = 1,
    timeout_sec: float = 2.0,
) -> str:
    """Read raw text lines from a serial sensor (e.g. Arduino, GPS, range sensor).

    Args:
        port: Serial device path, e.g. '/dev/ttyUSB0'.
        baudrate: Serial baud rate (default 115200).
        num_lines: Number of lines to read.
        timeout_sec: Read timeout per line.

    Returns:
        JSON with lines read from the sensor.
    """
    try:
        import serial  # type: ignore[import]
    except ImportError:
        return json.dumps({"error": "pyserial not installed. Run: pip install pyserial"})

    if not Path(port).exists():
        return json.dumps({"error": f"Serial port {port} not found."})

    try:
        with serial.Serial(port, baudrate=baudrate, timeout=timeout_sec) as ser:
            lines = []
            for _ in range(num_lines):
                raw = ser.readline()
                if raw:
                    lines.append(raw.decode("utf-8", errors="replace").strip())
        return json.dumps({"port": port, "lines": lines})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("read_lidar_scan")
def read_lidar_scan_tool(topic: str = "/scan", timeout_sec: float = 3.0) -> str:
    """Read a single LiDAR scan from a ROS2 LaserScan topic.

    Args:
        topic: ROS2 topic publishing sensor_msgs/msg/LaserScan.
        timeout_sec: How long to wait for a scan.

    Returns:
        JSON with scan metadata: angle range, ranges summary, num_points.
    """
    import shutil
    import subprocess

    if not shutil.which("ros2"):
        return json.dumps({"error": "ROS2 not available."})
    try:
        out = subprocess.check_output(
            ["ros2", "topic", "echo", "--once", "--no-arr", topic],
            timeout=timeout_sec + 1,
            text=True,
        )
        return json.dumps({"topic": topic, "scan": out.strip()})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"No scan received on {topic} within {timeout_sec}s"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("identify_user_face")
def identify_user_face_tool(image_path: str = "", tolerance: float = 0.6) -> str:
    """Identify the user from a camera frame using face recognition.

    If image_path is empty, captures a new frame from the first camera.

    Args:
        image_path: Path to an image file. If empty, captures from camera 0.
        tolerance: Face matching tolerance (lower = stricter). Default 0.6.

    Returns:
        JSON with user_id (or 'unknown') and recognition details.
    """
    try:
        if not image_path:
            import json as _json
            import tempfile

            from deerflow.eaib.occipital_parietal.camera_tool import capture_frame_tool

            tmp = tempfile.mktemp(suffix=".jpg")
            raw = capture_frame_tool.invoke({"device_index": 0, "save_path": tmp, "return_base64": False})  # type: ignore[attr-defined]
            result = _json.loads(raw)
            if "error" in result:
                return raw
            image_path = result["path"]

        from deerflow.eaib.occipital_parietal.face_recognizer import get_face_recognizer

        recognizer = get_face_recognizer()
        return json.dumps(recognizer.identify(image_path, tolerance=tolerance))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("enroll_user_face")
def enroll_user_face_tool(user_id: str, image_path: str = "") -> str:
    """Enroll a user's face into the recognition database.

    If image_path is empty, captures a new frame from the first camera.

    Args:
        user_id: Unique identifier for the user (e.g. 'alice').
        image_path: Path to a clear front-facing photo. Captures from camera if empty.

    Returns:
        JSON confirming enrolment or describing the error.
    """
    try:
        if not image_path:
            import json as _json
            import tempfile

            from deerflow.eaib.occipital_parietal.camera_tool import capture_frame_tool

            tmp = tempfile.mktemp(suffix=".jpg")
            raw = capture_frame_tool.invoke({"device_index": 0, "save_path": tmp, "return_base64": False})  # type: ignore[attr-defined]
            result = _json.loads(raw)
            if "error" in result:
                return raw
            image_path = result["path"]

        from deerflow.eaib.occipital_parietal.face_recognizer import get_face_recognizer

        recognizer = get_face_recognizer()
        return json.dumps(recognizer.enroll(user_id, image_path))
    except Exception as e:
        return json.dumps({"error": str(e)})
