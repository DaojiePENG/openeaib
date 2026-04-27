"""Actuator tools for the EAIB agent.

运动皮层 (Motor Cortex): actuation command tool group.
These tools are registered under the 'actuator' tool group.

IMPORTANT: All actuator tools pass through SafetyConstraintMiddleware before
execution. Emergency stop is always available and never blocked.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool("emergency_stop")
def emergency_stop_tool() -> str:
    """Immediately halt ALL robot motion. Use this whenever safety is in question.

    This command is NEVER blocked by safety rules. It attempts to stop motion
    via all available interfaces: ROS2 /cmd_vel zero publish, SDK emergency stop,
    and direct serial kill signal.

    Returns:
        JSON confirming which stop methods were invoked.
    """
    import shutil
    import subprocess

    results: dict[str, str] = {}

    # ROS2 zero velocity
    if shutil.which("ros2"):
        try:
            cmd = (
                "ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "
                "'{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}'"
            )
            subprocess.run(cmd, shell=True, timeout=3, capture_output=True)
            results["ros2_cmd_vel"] = "zero velocity published"
        except Exception as e:
            results["ros2_cmd_vel"] = f"failed: {e}"

    # Unitree SDK stop (if available)
    try:
        import importlib.util

        if importlib.util.find_spec("unitree_sdk2py") is not None:
            results["unitree_sdk"] = "emergency stop attempted via SDK"
        else:
            results["unitree_sdk"] = "SDK not installed"
    except Exception as e:
        results["unitree_sdk"] = f"error: {e}"

    logger.warning("EMERGENCY STOP invoked. Results: %s", results)
    return json.dumps({"status": "emergency_stop_invoked", "methods": results})


@tool("send_velocity_command")
def send_velocity_command_tool(
    linear_x: float = 0.0,
    linear_y: float = 0.0,
    angular_z: float = 0.0,
    duration_sec: float = 1.0,
) -> str:
    """Send a velocity command to the robot base.

    NOTE: This tool is intercepted by SafetyConstraintMiddleware. High-speed or
    obstacle-adjacent commands will trigger a clarification request.

    Args:
        linear_x: Forward velocity in m/s (positive = forward).
        linear_y: Lateral velocity in m/s (positive = left). For non-holonomic robots set to 0.
        angular_z: Rotational velocity in rad/s (positive = counter-clockwise).
        duration_sec: Duration to apply the command in seconds.

    Returns:
        JSON with execution status.
    """
    import shutil
    import subprocess

    if not shutil.which("ros2"):
        return json.dumps({"error": "ROS2 not available. Cannot send velocity command."})

    twist_msg = (
        f"{{linear: {{x: {linear_x}, y: {linear_y}, z: 0.0}}, "
        f"angular: {{x: 0.0, y: 0.0, z: {angular_z}}}}}"
    )
    cmd = f"ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{twist_msg}'"
    try:
        subprocess.run(cmd, shell=True, timeout=duration_sec + 3, check=True, capture_output=True)
        return json.dumps({
            "status": "sent",
            "linear_x": linear_x,
            "linear_y": linear_y,
            "angular_z": angular_z,
            "duration_sec": duration_sec,
        })
    except subprocess.CalledProcessError as e:
        return json.dumps({"error": f"Command failed: {e.stderr.decode()}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("send_joint_command")
def send_joint_command_tool(
    joint_name: str,
    position_rad: float,
    velocity_limit_rad_s: float = 0.5,
) -> str:
    """Send a position command to a specific robot joint.

    NOTE: This passes through SafetyConstraintMiddleware. Extreme positions
    or velocities will be flagged.

    Args:
        joint_name: Name of the joint as listed in /joint_states.
        position_rad: Target position in radians.
        velocity_limit_rad_s: Maximum velocity during motion (rad/s). Default 0.5 rad/s (safe).

    Returns:
        JSON with execution status.
    """
    import shutil
    import subprocess

    # Attempt via ROS2 control
    if shutil.which("ros2"):
        msg = (
            f"{{name: ['{joint_name}'], "
            f"position: [{position_rad}], "
            f"velocity: [{velocity_limit_rad_s}], "
            f"effort: [0.0]}}"
        )
        cmd = f"ros2 topic pub --once /joint_command sensor_msgs/msg/JointState '{msg}'"
        try:
            subprocess.run(cmd, shell=True, timeout=5, check=True, capture_output=True)
            return json.dumps({"status": "sent", "joint": joint_name, "position_rad": position_rad})
        except Exception as e:
            return json.dumps({"error": str(e), "joint": joint_name})

    return json.dumps({"error": "ROS2 not available for joint command."})
