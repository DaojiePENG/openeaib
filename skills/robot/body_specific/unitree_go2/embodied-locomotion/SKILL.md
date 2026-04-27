---
name: unitree-go2-locomotion
description: >
  Locomotion skill for the Unitree Go2 quadruped robot.
  Covers stand-up, walk, trot, turn, and stop using the unitree_sdk2py SDK.
  Requires body_id='unitree_go2' with the unitree_sdk2py SDK adapter registered.
category: robot-body-specific
body_id: unitree_go2
---

# Skill: Unitree Go2 Locomotion

## Prerequisites
- SDK adapter registered: `body_id = "unitree_go2"`, `sdk_package = "unitree_sdk2py"`
- Go2 powered on, booted, on flat surface
- Ethernet or WiFi connected to Go2 (default IP: `192.168.123.161`)

## SDK Reference
```python
pip install unitree_sdk2py

from unitree_sdk2py.go2.sport.sport_client import SportClient
```

## Stand
```python
from unitree_sdk2py.go2.sport.sport_client import SportClient

def stand(host: str = "192.168.123.161") -> dict:
    client = SportClient()
    client.SetTimeout(10.0)
    client.Init()
    client.StandUp()
    return {"status": "ok", "posture": "stand"}
```

## Walk Forward
```python
def walk_forward(
    host: str = "192.168.123.161",
    speed_ms: float = 0.5,
    duration_s: float = 2.0,
) -> dict:
    import time
    client = SportClient()
    client.SetTimeout(10.0)
    client.Init()
    client.Move(speed_ms, 0.0, 0.0)
    time.sleep(duration_s)
    client.Move(0.0, 0.0, 0.0)
    return {"status": "ok", "distance_approx_m": speed_ms * duration_s}
```

## Trot (faster gait)
```python
def trot(
    host: str = "192.168.123.161",
    speed_ms: float = 1.0,
    duration_s: float = 3.0,
) -> dict:
    """Switch Go2 to trot gait for faster movement."""
    import time
    client = SportClient()
    client.SetTimeout(10.0)
    client.Init()
    client.SwitchGait(2)         # 2 = trot (check your SDK version)
    client.Move(speed_ms, 0.0, 0.0)
    time.sleep(duration_s)
    client.Move(0.0, 0.0, 0.0)
    client.SwitchGait(0)         # 0 = idle/walk
    return {"status": "ok"}
```

## Turn
```python
def turn(
    host: str = "192.168.123.161",
    yaw_rad_s: float = 0.5,
    duration_s: float = 2.0,
) -> dict:
    import time
    client = SportClient()
    client.SetTimeout(10.0)
    client.Init()
    client.Move(0.0, 0.0, yaw_rad_s)
    time.sleep(duration_s)
    client.Move(0.0, 0.0, 0.0)
    return {"status": "ok"}
```

## Sit Down (rest posture)
```python
def sit(host: str = "192.168.123.161") -> dict:
    client = SportClient()
    client.SetTimeout(10.0)
    client.Init()
    client.StandDown()
    return {"status": "ok", "posture": "sit"}
```

## Safety Checklist
- [ ] Flat, obstacle-free surface
- [ ] Battery > 25% for any motion sequence
- [ ] Test walk at ≤ 0.2 m/s first
- [ ] `emergency_stop_tool` ready during tests

## Error Recovery
| Error | Remedy |
|---|---|
| `ConnectionRefusedError` | `ping 192.168.123.161`; check Wi-Fi/cable |
| Go2 doesn't move | Confirm `StandUp()` completed before `Move()` |
| Leg slip / fall | Call `emergency_stop_tool`; restart Go2 |
| Wrong gait number | Check SDK changelog for your firmware version |
