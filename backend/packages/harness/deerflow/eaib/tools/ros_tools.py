"""ROS2 tools for the EAIB agent.

运动皮层 (Motor Cortex): ROS2 interaction tool group.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _ros2_available() -> bool:
    return shutil.which("ros2") is not None


@tool("ros_topic_list")
def ros_topic_list_tool() -> str:
    """List all active ROS2 topics.

    Returns:
        JSON list of topic names, or an error message if ROS2 is unavailable.
    """
    if not _ros2_available():
        return json.dumps({"error": "ROS2 not available in PATH."})
    try:
        out = subprocess.check_output(["ros2", "topic", "list"], timeout=5, text=True)
        topics = [t.strip() for t in out.splitlines() if t.strip()]
        return json.dumps({"topics": topics, "count": len(topics)})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("ros_topic_echo")
def ros_topic_echo_tool(topic: str, msg_type: str = "", timeout_sec: float = 3.0) -> str:
    """Echo a single message from a ROS2 topic.

    Args:
        topic: Full topic name, e.g. '/camera/image_raw'.
        msg_type: Optional message type, e.g. 'sensor_msgs/msg/Image'. Auto-detected if empty.
        timeout_sec: Seconds to wait for a message.

    Returns:
        JSON with the raw echoed message.
    """
    if not _ros2_available():
        return json.dumps({"error": "ROS2 not available."})
    cmd = ["ros2", "topic", "echo", "--once", "--no-arr", topic]
    if msg_type:
        cmd.append(msg_type)
    try:
        out = subprocess.check_output(cmd, timeout=timeout_sec + 1, text=True)
        return json.dumps({"topic": topic, "message": out.strip()})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"No message received on {topic} within {timeout_sec}s"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("ros_service_call")
def ros_service_call_tool(service: str, srv_type: str, request: str = "{}") -> str:
    """Call a ROS2 service.

    Args:
        service: Service name, e.g. '/robot/set_mode'.
        srv_type: Service type, e.g. 'std_srvs/srv/SetBool'.
        request: YAML/JSON request body, e.g. '{data: true}'.

    Returns:
        JSON with the service response.
    """
    if not _ros2_available():
        return json.dumps({"error": "ROS2 not available."})
    try:
        out = subprocess.check_output(
            ["ros2", "service", "call", service, srv_type, request],
            timeout=10,
            text=True,
        )
        return json.dumps({"service": service, "response": out.strip()})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("ros_launch")
def ros_launch_tool(package: str, launch_file: str, args: str = "") -> str:
    """Launch a ROS2 launch file in the background.

    Args:
        package: ROS2 package name, e.g. 'unitree_ros'.
        launch_file: Launch file name, e.g. 'robot_bringup.launch.py'.
        args: Space-separated launch arguments, e.g. 'use_sim:=true'.

    Returns:
        JSON with the PID of the launched process.
    """
    if not _ros2_available():
        return json.dumps({"error": "ROS2 not available."})
    cmd = ["ros2", "launch", package, launch_file]
    if args:
        cmd.extend(args.split())
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.dumps({"status": "launched", "pid": proc.pid, "command": " ".join(cmd)})
    except Exception as e:
        return json.dumps({"error": str(e)})
