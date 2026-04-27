"""Sensor tools for the EAIB agent.

运动皮层 (Motor Cortex): sensor reading tool group.
These tools are registered under the 'sensor' tool group.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool("list_sensors")
def list_sensors_tool() -> str:
    """List all sensors and hardware peripherals detected on the current robot body.

    Returns a JSON summary of available sensors including cameras, LiDAR, IMU,
    ROS2 topics, GPU, CPU/RAM, and any connected serial devices.
    """
    try:
        from deerflow.eaib.body.hardware_scanner import get_hardware_scanner

        scanner = get_hardware_scanner()
        summary = scanner.scan_summary()
        return json.dumps(summary, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "sensors": []})


@tool("read_imu")
def read_imu_tool(topic: str = "/imu/data", timeout_sec: float = 2.0) -> str:
    """Read a single IMU measurement from the robot.

    Args:
        topic: ROS2 topic name for IMU data. Default '/imu/data'.
        timeout_sec: Timeout in seconds to wait for a message.

    Returns:
        JSON with orientation (quaternion), angular velocity, and linear acceleration.
    """
    import subprocess
    import shutil

    if not shutil.which("ros2"):
        return json.dumps({"error": "ROS2 not available. Connect ROS2 or ensure 'ros2' is in PATH."})
    try:
        out = subprocess.check_output(
            ["ros2", "topic", "echo", "--once", "--no-arr", topic, "sensor_msgs/msg/Imu"],
            timeout=timeout_sec + 1,
            text=True,
        )
        return json.dumps({"topic": topic, "raw": out.strip()})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Timeout waiting for IMU data on {topic}"})
    except Exception as e:
        return json.dumps({"error": str(e), "topic": topic})


@tool("read_odometry")
def read_odometry_tool(topic: str = "/odom", timeout_sec: float = 2.0) -> str:
    """Read the current robot odometry (position + velocity).

    Args:
        topic: ROS2 topic for odometry. Default '/odom'.
        timeout_sec: Timeout in seconds.

    Returns:
        JSON with position (x, y, z), orientation (quaternion), and velocity.
    """
    import subprocess
    import shutil

    if not shutil.which("ros2"):
        return json.dumps({"error": "ROS2 not available."})
    try:
        out = subprocess.check_output(
            ["ros2", "topic", "echo", "--once", "--no-arr", topic, "nav_msgs/msg/Odometry"],
            timeout=timeout_sec + 1,
            text=True,
        )
        return json.dumps({"topic": topic, "raw": out.strip()})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Timeout on {topic}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("read_joint_states")
def read_joint_states_tool(topic: str = "/joint_states", timeout_sec: float = 2.0) -> str:
    """Read current joint positions, velocities, and efforts from the robot.

    Args:
        topic: ROS2 topic for joint states. Default '/joint_states'.
        timeout_sec: Timeout in seconds.

    Returns:
        JSON with joint names, positions, velocities, and efforts.
    """
    import subprocess
    import shutil

    if not shutil.which("ros2"):
        return json.dumps({"error": "ROS2 not available."})
    try:
        out = subprocess.check_output(
            ["ros2", "topic", "echo", "--once", "--no-arr", topic, "sensor_msgs/msg/JointState"],
            timeout=timeout_sec + 1,
            text=True,
        )
        return json.dumps({"topic": topic, "raw": out.strip()})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Timeout on {topic}"})
    except Exception as e:
        return json.dumps({"error": str(e)})
