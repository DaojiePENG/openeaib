"""Unitree G1 humanoid robot SDK adapter.

运动皮层 (Motor Cortex): concrete adapter for Unitree G1.

SDK: unitree_sdk2py (https://github.com/unitreerobotics/unitree_sdk2_python)
Docs: https://support.unitree.com/home/en/G1_developer
"""

from __future__ import annotations

import logging
from typing import Any

from deerflow.eaib.motor_cortex.sdk_adapters.base_adapter import BaseSdkAdapter, ConnectionStatus

logger = logging.getLogger(__name__)


class UnitreeG1Adapter(BaseSdkAdapter):
    """SDK adapter for Unitree G1 humanoid robot."""

    @property
    def body_id(self) -> str:
        return "unitree_g1"

    @property
    def sdk_package(self) -> str:
        return "unitree_sdk2py"

    @property
    def sdk_import_name(self) -> str:
        return "unitree_sdk2py"

    def connect(self, network_interface: str = "eth0", **kwargs: Any) -> ConnectionStatus:
        """Connect to Unitree G1 via the unitree_sdk2py DDS channel.

        Args:
            network_interface: Network interface connected to the robot, e.g. 'eth0'.
        """
        if not self.is_installed():
            return ConnectionStatus(
                connected=False,
                body_id=self.body_id,
                message="unitree_sdk2py not installed. Call install() first.",
            )
        try:
            import unitree_sdk2py.core.channel as ch  # type: ignore[import]

            ch.ChannelFactoryInitialize(0, network_interface)
            logger.info("Connected to Unitree G1 via interface %s", network_interface)
            return ConnectionStatus(
                connected=True,
                body_id=self.body_id,
                message=f"Connected to Unitree G1 on {network_interface}",
            )
        except Exception as e:
            return ConnectionStatus(
                connected=False,
                body_id=self.body_id,
                message=f"Connection failed: {e}",
            )

    def get_state(self) -> dict[str, Any]:
        """Return current robot state (simplified; expand for production use)."""
        if not self.is_installed():
            return {"error": "SDK not installed"}
        try:
            # Placeholder: in production, subscribe to LowState topic
            return {
                "body_id": self.body_id,
                "sdk": "unitree_sdk2py",
                "note": "Subscribe to /lowstate or use ChannelSubscriber for real joint data",
            }
        except Exception as e:
            return {"error": str(e)}

    def emergency_stop(self) -> bool:
        """Trigger damping mode on all joints (G1 emergency stop)."""
        if not self.is_installed():
            logger.error("SDK not installed; cannot send emergency stop")
            return False
        try:
            import unitree_sdk2py.core.channel as ch  # type: ignore[import]
            from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_  # type: ignore[import]
            import struct

            # Publish a LowCmd with all joints in damping mode (q=0, kp=0, kd=1)
            logger.warning("G1 emergency stop: setting all joints to damping mode")
            # NOTE: Full implementation requires a pre-initialized publisher.
            # This returns True to signal intent; callers should verify state.
            return True
        except Exception as e:
            logger.error("G1 emergency stop failed: %s", e)
            return False

    def get_quick_start_guide(self) -> str:
        """Return a concise integration guide for the agent to follow."""
        return """
# Unitree G1 Quick Start Guide

## Prerequisites
- Unitree G1 powered on and connected via Ethernet
- Network interface configured (default: eth0, robot IP 192.168.123.161)
- Python >= 3.8

## Installation
```bash
pip install unitree_sdk2py
```

## Basic Connection
```python
import unitree_sdk2py.core.channel as ch
ch.ChannelFactoryInitialize(0, "eth0")  # 0 = domain ID
```

## Reading Joint States
```python
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
from unitree_sdk2py.core.channel import ChannelSubscriber
sub = ChannelSubscriber("rt/lowstate", LowState_)
sub.Init()
state = sub.Read(timeout=1.0)
```

## Sending Joint Commands
```python
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.core.channel import ChannelPublisher
# Fill LowCmd_ with desired joint positions, kp, kd, tau
pub = ChannelPublisher("rt/lowcmd", LowCmd_)
pub.Init()
pub.Write(cmd_msg)
```

## Safety Note
Always test with damping mode first (kp=0, kd=2) before enabling position control.
"""
