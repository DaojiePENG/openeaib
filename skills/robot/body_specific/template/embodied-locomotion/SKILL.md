---
name: embodied-locomotion
description: >
  Template skill for teaching a robot body how to perform basic locomotion tasks:
  standing, walking, turning, and stopping. Copy this SKILL.md to
  skills/robot/body_specific/<body_id>/embodied-locomotion/ and fill in the
  body-specific SDK calls.
category: robot-body-specific
body_id: template
---

# Skill: Embodied Locomotion (Template)

## Prerequisite
- Body adapter registered and connected (`test_robot_adapter` returns `connected: true`)
- SDK installed (`install_robot_sdk` run successfully)

## Overview
This skill template covers:
1. **Stand up** — transition from rest to standing posture
2. **Walk forward** — issue velocity commands
3. **Turn** — rotate in place
4. **Stop** — controlled halt (not emergency stop)

---

## Stand Up
```python
# Replace with body-specific SDK call
def stand_up(adapter) -> dict:
    # Example: adapter.sdk_client.set_gait("stand")
    raise NotImplementedError("Fill in body-specific stand-up call")
```

## Walk Forward
```python
def walk_forward(adapter, speed_ms: float = 0.3, duration_s: float = 2.0) -> dict:
    # Example via velocity command:
    #   send_velocity_command_tool(linear_x=speed_ms, angular_z=0.0)
    raise NotImplementedError("Fill in body-specific walk forward call")
```

## Turn In Place
```python
def turn(adapter, angular_rad_s: float = 0.3, duration_s: float = 2.0) -> dict:
    raise NotImplementedError("Fill in body-specific turn call")
```

## Stop
```python
def stop(adapter) -> dict:
    # Controlled stop (not emergency)
    raise NotImplementedError("Fill in body-specific controlled stop call")
```

---

## Common Pitfalls
- Send stand-up command before walking; most SDK clients require the robot to be in stand mode
- Use small velocity values (< 0.5 m/s) for initial tests
- Duration-based motion: use `time.sleep(duration_s)` + stop, or SDK's built-in blocking call
- For ROS-based robots: publish to `/cmd_vel` topic instead of calling SDK directly

## Testing Checklist
- [ ] Robot stands on flat surface with > 20 cm clearance in all directions
- [ ] `stand_up` executed and robot reaches upright posture within 3 seconds
- [ ] `walk_forward(speed_ms=0.1, duration_s=1.0)` moves approx. 0.1 m
- [ ] `stop()` halts motion smoothly
- [ ] No joint error flags in `get_state()` after execution
