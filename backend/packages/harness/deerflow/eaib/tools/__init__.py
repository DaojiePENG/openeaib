"""EAIB tools sub-package."""

from deerflow.eaib.tools.actuator_tools import (
    emergency_stop_tool,
    send_joint_command_tool,
    send_velocity_command_tool,
)
from deerflow.eaib.tools.adapter_tools import (
    get_adapter_code_tool,
    get_adapter_template_tool,
    install_robot_sdk_tool,
    list_robot_adapters_tool,
    register_robot_adapter_tool,
    remove_robot_adapter_tool,
    test_robot_adapter_tool,
)
from deerflow.eaib.tools.ros_tools import (
    ros_launch_tool,
    ros_service_call_tool,
    ros_topic_echo_tool,
    ros_topic_list_tool,
)
from deerflow.eaib.tools.sensor_tools import (
    list_sensors_tool,
    read_imu_tool,
    read_joint_states_tool,
    read_odometry_tool,
)
from deerflow.eaib.tools.skill_tools import (
    archive_robot_skill_tool,
    list_robot_skills_tool,
    record_skill_execution_tool,
    save_robot_skill_tool,
    search_robot_skills_tool,
)

SENSOR_TOOLS = [
    list_sensors_tool,
    read_imu_tool,
    read_odometry_tool,
    read_joint_states_tool,
]

ACTUATOR_TOOLS = [
    emergency_stop_tool,
    send_velocity_command_tool,
    send_joint_command_tool,
]

ROS_TOOLS = [
    ros_topic_list_tool,
    ros_topic_echo_tool,
    ros_service_call_tool,
    ros_launch_tool,
]

SKILL_TOOLS = [
    list_robot_skills_tool,
    search_robot_skills_tool,
    save_robot_skill_tool,
    record_skill_execution_tool,
    archive_robot_skill_tool,
]

# Tools for dynamic hardware onboarding (no pre-built robot knowledge assumed)
ADAPTER_TOOLS = [
    list_robot_adapters_tool,
    get_adapter_template_tool,
    register_robot_adapter_tool,
    install_robot_sdk_tool,
    test_robot_adapter_tool,
    get_adapter_code_tool,
    remove_robot_adapter_tool,
]

ALL_EAIB_TOOLS = SENSOR_TOOLS + ACTUATOR_TOOLS + ROS_TOOLS + SKILL_TOOLS + ADAPTER_TOOLS

__all__ = [
    "SENSOR_TOOLS",
    "ACTUATOR_TOOLS",
    "ROS_TOOLS",
    "SKILL_TOOLS",
    "ADAPTER_TOOLS",
    "ALL_EAIB_TOOLS",
]
