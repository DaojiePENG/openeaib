"""Adapter management tools for the motor cortex agent.

These tools let the agent discover, create, and register SDK adapters for
ANY robot hardware through conversation with the user — no pre-built knowledge
of specific robots is assumed.

Workflow:
1. User describes robot model and SDK
2. Agent calls `get_adapter_template` to get a blank code template
3. Agent fills in the template (using bash to read SDK docs / pip show, etc.)
4. Agent writes the code to a file using write_file / bash
5. Agent calls `register_robot_adapter` to persist and activate it
6. Agent calls `test_robot_adapter` to verify installation + connection
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool("list_robot_adapters")
def list_robot_adapters_tool() -> str:
    """List all currently registered robot SDK adapters.

    Returns information about adapters the system knows how to use.
    An empty list is normal when no robot has been configured yet.

    Returns:
        JSON list of adapter summaries with body_id, sdk_package, installed status.
    """
    try:
        from deerflow.eaib.motor_cortex.sdk_adapters import get_adapter_registry

        registry = get_adapter_registry()
        adapters = registry.list_all()
        unregistered = registry.discover_unregistered()
        return json.dumps({
            "registered": adapters,
            "unregistered_on_disk": unregistered,
            "total": len(adapters),
            "note": "Call register_robot_adapter to activate any unregistered adapters." if unregistered else "",
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("get_adapter_template")
def get_adapter_template_tool(body_id: str, sdk_package: str = "UNKNOWN") -> str:
    """Generate a blank SDK adapter code template for a new robot.

    Use this as the starting point when implementing support for a new robot.
    Edit the template to fill in connection, state reading, and emergency stop logic.

    Args:
        body_id: Unique identifier for this robot, e.g. 'my_arm_v2', 'boston_spot'.
        sdk_package: Pip package name for the SDK, e.g. 'spot-sdk'. Use 'UNKNOWN' if unsure.

    Returns:
        Python source code template that you should fill in and then register.
    """
    try:
        from deerflow.eaib.motor_cortex.sdk_adapters import get_adapter_registry

        registry = get_adapter_registry()
        code = registry.get_example_template(body_id=body_id, sdk_package=sdk_package)
        return json.dumps({"body_id": body_id, "template_code": code})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("register_robot_adapter")
def register_robot_adapter_tool(body_id: str, adapter_py_path: str, notes: str = "") -> str:
    """Register a generated SDK adapter file for a robot body.

    Call this after writing the adapter.py file to disk.
    The file will be validated (imported) before registration.

    Args:
        body_id: Robot body identifier, e.g. 'my_arm_v2'.
        adapter_py_path: Absolute path to the generated adapter.py file.
        notes: Optional notes about this adapter (shown in list_robot_adapters).

    Returns:
        JSON confirming registration or describing the error.
    """
    try:
        from deerflow.eaib.motor_cortex.sdk_adapters import get_adapter_registry

        registry = get_adapter_registry()
        ok = registry.register_from_file(body_id=body_id, adapter_py_path=Path(adapter_py_path), notes=notes)
        if ok:
            adapter = registry.get(body_id)
            return json.dumps({
                "registered": True,
                "body_id": body_id,
                "sdk_package": adapter.sdk_package if adapter else "unknown",
                "installed": adapter.is_installed() if adapter else False,
                "hint": "Call install_robot_sdk to install the SDK package if installed=false.",
            })
        return json.dumps({"registered": False, "body_id": body_id, "error": "Validation failed — check adapter code."})
    except Exception as e:
        return json.dumps({"registered": False, "error": str(e)})


@tool("install_robot_sdk")
def install_robot_sdk_tool(body_id: str) -> str:
    """Install the SDK for a registered robot adapter.

    Args:
        body_id: Robot body identifier whose SDK should be installed.

    Returns:
        JSON with installation result.
    """
    try:
        from deerflow.eaib.motor_cortex.sdk_adapters import get_adapter_registry

        registry = get_adapter_registry()
        adapter = registry.get(body_id)
        if adapter is None:
            return json.dumps({"error": f"No adapter registered for body_id='{body_id}'. Call register_robot_adapter first."})

        if adapter.is_installed():
            return json.dumps({"installed": True, "body_id": body_id, "note": "SDK already installed."})

        ok, msg = adapter.install()
        return json.dumps({"installed": ok, "body_id": body_id, "message": msg})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("test_robot_adapter")
def test_robot_adapter_tool(body_id: str, connect_kwargs: str = "{}") -> str:
    """Test a registered robot adapter: check SDK installation and attempt connection.

    Args:
        body_id: Robot body identifier to test.
        connect_kwargs: JSON string of keyword arguments passed to adapter.connect(),
                        e.g. '{"network_interface": "eth0"}' or '{"host": "192.168.1.100"}'.

    Returns:
        JSON with installation status, connection result, and current state snapshot.
    """
    try:
        import json as _json

        from deerflow.eaib.motor_cortex.sdk_adapters import get_adapter_registry

        registry = get_adapter_registry()
        adapter = registry.get(body_id)
        if adapter is None:
            return json.dumps({"error": f"No adapter for body_id='{body_id}'."})

        installed = adapter.is_installed()
        result: dict = {"body_id": body_id, "installed": installed}

        if not installed:
            result["connection"] = {"connected": False, "message": "SDK not installed. Call install_robot_sdk first."}
            return json.dumps(result)

        kwargs = _json.loads(connect_kwargs) if connect_kwargs.strip() not in ("", "{}") else {}
        status = adapter.connect(**kwargs)
        result["connection"] = {
            "connected": status.connected,
            "message": status.message,
            "sdk_version": status.sdk_version,
        }

        if status.connected:
            try:
                state = adapter.get_state()
                result["state_snapshot"] = state
            except Exception as se:
                result["state_snapshot"] = {"error": str(se)}

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("get_adapter_code")
def get_adapter_code_tool(body_id: str) -> str:
    """Read the current adapter.py source code for a registered body.

    Useful for inspecting or editing an existing adapter.

    Args:
        body_id: Robot body identifier.

    Returns:
        JSON with the adapter source code string, or an error.
    """
    try:
        from deerflow.eaib.motor_cortex.sdk_adapters import get_adapter_registry

        registry = get_adapter_registry()
        code = registry.get_adapter_code(body_id)
        if code is None:
            return json.dumps({"error": f"No adapter.py found for body_id='{body_id}'."})
        return json.dumps({"body_id": body_id, "code": code})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("remove_robot_adapter")
def remove_robot_adapter_tool(body_id: str, delete_files: bool = False) -> str:
    """Remove a robot adapter from the registry.

    Args:
        body_id: Robot body identifier to remove.
        delete_files: If true, also delete the adapter.py and meta.json from disk.

    Returns:
        JSON confirming removal.
    """
    try:
        from deerflow.eaib.motor_cortex.sdk_adapters import get_adapter_registry

        registry = get_adapter_registry()
        ok = registry.remove(body_id=body_id, delete_files=delete_files)
        return json.dumps({"removed": ok, "body_id": body_id, "files_deleted": delete_files and ok})
    except Exception as e:
        return json.dumps({"error": str(e)})
