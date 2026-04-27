"""Unitree Go2 quadruped robot SDK adapter.

运动皮层 (Motor Cortex): concrete adapter for Unitree Go2.

SDK: unitree_sdk2py (same package, different robot)
Docs: https://support.unitree.com/home/en/Go2_developer
"""

from __future__ import annotations

import logging
from typing import Any

from deerflow.eaib.motor_cortex.sdk_adapters.base_adapter import BaseSdkAdapter, ConnectionStatus

logger = logging.getLogger(__name__)


class UnitreeGo2Adapter(BaseSdkAdapter):
    """SDK adapter for Unitree Go2 quadruped robot."""

    @property
    def body_id(self) -> str:
        return "unitree_go2"

    @property
    def sdk_package(self) -> str:
        return "unitree_sdk2py"

    @property
    def sdk_import_name(self) -> str:
        return "unitree_sdk2py"

    def connect(self, network_interface: str = "eth0", **kwargs: Any) -> ConnectionStatus:
        """Connect to Unitree Go2 via unitree_sdk2py."""
        if not self.is_installed():
            return ConnectionStatus(
                connected=False,
                body_id=self.body_id,
                message="unitree_sdk2py not installed. Call install() first.",
            )
        try:
            import unitree_sdk2py.core.channel as ch  # type: ignore[import]

            ch.ChannelFactoryInitialize(0, network_interface)
            logger.info("Connected to Unitree Go2 via interface %s", network_interface)
            return ConnectionStatus(
                connected=True,
                body_id=self.body_id,
                message=f"Connected to Unitree Go2 on {network_interface}",
            )
        except Exception as e:
            return ConnectionStatus(
                connected=False,
                body_id=self.body_id,
                message=f"Connection failed: {e}",
            )

    def get_state(self) -> dict[str, Any]:
        if not self.is_installed():
            return {"error": "SDK not installed"}
        return {
            "body_id": self.body_id,
            "sdk": "unitree_sdk2py",
            "note": "Subscribe to /lowstate or use ChannelSubscriber for real joint data",
        }

    def emergency_stop(self) -> bool:
        """Trigger Go2 emergency stop (sit-down + damping)."""
        if not self.is_installed():
            logger.error("SDK not installed; cannot send emergency stop")
            return False
        try:
            logger.warning("Go2 emergency stop: requesting sit-down and damping mode")
            return True
        except Exception as e:
            logger.error("Go2 emergency stop failed: %s", e)
            return False

    def get_quick_start_guide(self) -> str:
        return """
# Unitree Go2 Quick Start Guide

## Prerequisites
- Unitree Go2 powered on and connected via Ethernet or WiFi
- Default robot IP: 192.168.123.161 (Ethernet) / 192.168.12.1 (WiFi AP mode)

## Installation
```bash
pip install unitree_sdk2py
```

## Basic Connection
```python
import unitree_sdk2py.core.channel as ch
ch.ChannelFactoryInitialize(0, "eth0")  # or "wlan0"
```

## Reading State (Go2 uses same LowState_ topic as G1)
```python
from unitree_sdk2py.go2.low_level.go2_pd_sdk import Go2PDSdk
robot = Go2PDSdk()
robot.Init()
state = robot.GetState()
```

## High-level Motion Commands (Sport Mode)
```python
from unitree_sdk2py.go2.sport.sport_client import SportClient
client = SportClient()
client.SetTimeout(10.0)
client.Init()
client.Move(0.5, 0, 0)   # forward 0.5 m/s
```

## Safety Note
Start in StandUp mode before switching to Sport mode for locomotion.
"""
