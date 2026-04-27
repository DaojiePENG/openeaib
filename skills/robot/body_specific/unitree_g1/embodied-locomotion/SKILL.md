---
name: unitree-g1-locomotion
description: >
  Locomotion skill for the Unitree G1 humanoid robot.
  Covers stand-up, walk, turn, and controlled stop using the unitree_sdk2py SDK.
  Requires body_id='unitree_g1' with the unitree_sdk2py SDK adapter registered.
category: robot-body-specific
body_id: unitree_g1
---

# Skill: Unitree G1 Locomotion

## Prerequisites
- SDK adapter registered: `body_id = "unitree_g1"`, `sdk_package = "unitree_sdk2py"`
- Adapter connected: `test_robot_adapter(body_id="unitree_g1")` → `connected: true`
- G1 powered on and standing on flat surface

## SDK Reference
```python
# Install
pip install unitree_sdk2py

# Main movement class
from unitree_sdk2py.go2.sport.sport_client import SportClient
```

## Stand Up
```python
from unitree_sdk2py.go2.sport.sport_client import SportClient

def stand_up(host: str = "192.168.123.161") -> dict:
    """Transition G1 from rest to balanced standing."""
    client = SportClient()
    client.Init()
    client.StandUp()
    return {"status": "ok", "posture": "stand"}
```

## Walk Forward
```python
def walk_forward(
    host: str = "192.168.123.161",
    speed_ms: float = 0.3,
    duration_s: float = 2.0,
) -> dict:
    """Walk the G1 forward at given speed for given duration."""
    import time
    client = SportClient()
    client.Init()
    client.Move(speed_ms, 0.0, 0.0)  # vx, vy, vyaw
    time.sleep(duration_s)
    client.Move(0.0, 0.0, 0.0)       # stop
    return {"status": "ok", "distance_approx_m": speed_ms * duration_s}
```

## Turn In Place
```python
def turn(
    host: str = "192.168.123.161",
    yaw_rad_s: float = 0.3,
    duration_s: float = 2.0,
) -> dict:
    """Rotate G1 in place."""
    import time
    client = SportClient()
    client.Init()
    client.Move(0.0, 0.0, yaw_rad_s)
    time.sleep(duration_s)
    client.Move(0.0, 0.0, 0.0)
    return {"status": "ok", "angle_approx_rad": yaw_rad_s * duration_s}
```

## Controlled Stop
```python
def stop(host: str = "192.168.123.161") -> dict:
    """Smooth halt."""
    client = SportClient()
    client.Init()
    client.Move(0.0, 0.0, 0.0)
    return {"status": "ok"}
```

## Safety Checklist
- [ ] Clear area of obstacles ≥ 1 m in all directions
- [ ] Battery level > 30%
- [ ] First `walk_forward` test: speed ≤ 0.1 m/s, duration ≤ 1 s
- [ ] Keep emergency_stop_tool as hotkey during any motion test

## Error Recovery
| Error | Remedy |
|---|---|
| `ConnectionRefusedError` | Verify G1 IP; check ethernet cable; try `ping 192.168.123.161` |
| `RuntimeError: sdk not init` | Call `client.Init()` before any command |
| G1 falls / unbalanced | Call `emergency_stop_tool`; restart sport service on G1 |
