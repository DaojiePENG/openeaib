---
name: hardware-detection
description: >
  Guide the robot AI to auto-detect and onboard new hardware peripherals.
  Use this skill when: the user mentions a new robot or sensor; you need to
  scan the host for connected devices; or you want to register a new body profile.
category: robot-universal
---

# Skill: Hardware Detection & Onboarding

## When to Use
- User mentions a new robot, arm, sensor, or actuator
- System boots without a configured body
- User asks "what hardware do you see?" or "can you connect to my robot?"

## Workflow

### Step 1 — Scan host hardware
```python
# Call the list_sensors tool to see what the OS already exposes
list_sensors_tool()
```

### Step 2 — Identify the robot
Ask the user:
1. What is the robot model / name?
2. Does it have a Python SDK? (pip package or GitHub URL)
3. How does it connect? (Ethernet / USB / WiFi / CAN)
4. What is the IP address or device path?

### Step 3 — Register a body profile
```python
# Create a body entry in the registry
# (via API POST /api/eaib/body/register or body_registry.register())
register_body(body_id="my_robot", display_name="My Robot", hardware_type="custom")
```

### Step 4 — Create SDK adapter (delegate to motor-cortex)
```
Delegate to motor-cortex subagent:
"The user has a robot called <name>. SDK: <pkg>. Connection: <interface>.
Please create and register an SDK adapter for body_id='<id>'."
```

### Step 5 — Verify
```python
test_robot_adapter(body_id="my_robot", connect_kwargs='{"host": "192.168.x.x"}')
```

## Notes
- Always confirm with the user before sending any motion commands after onboarding
- Set the new body as current only after successful connection test
- Save hardware scan result in body metadata for future reference
