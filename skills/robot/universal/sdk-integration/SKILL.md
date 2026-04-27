---
name: sdk-integration
description: >
  Guide the robot AI to install, configure, and validate a new robot SDK.
  Use this skill when onboarding a new robot body that requires a custom SDK
  not already registered in the adapter registry.
category: robot-universal
---

# Skill: SDK Integration

## When to Use
- `list_robot_adapters` returns empty or no adapter for the target body
- User provides a new SDK package name or GitHub URL
- An existing adapter's `is_installed` is False

## Workflow

### Step 1 — Get the template
```python
get_adapter_template(body_id="my_robot", sdk_package="my_robot_sdk")
```

### Step 2 — Research the SDK
```bash
# Install and inspect
pip install my_robot_sdk
pip show my_robot_sdk
python -c "import my_robot_sdk; help(my_robot_sdk)"
```

Also check:
- Official documentation URL
- GitHub README / examples directory
- Any connection example scripts

### Step 3 — Fill in the adapter

Edit the template code to implement:

```python
def connect(self, **kwargs) -> ConnectionStatus:
    # Import the SDK and establish connection
    import my_robot_sdk
    client = my_robot_sdk.Client(kwargs.get("host", "192.168.1.100"))
    client.connect()
    return ConnectionStatus(connected=True, body_id=self.body_id, message="Connected")

def get_state(self) -> dict:
    # Return robot state: joints, battery, error flags, etc.
    return client.get_state()

def emergency_stop(self) -> bool:
    # Halt all motion immediately
    client.stop()
    return True
```

### Step 4 — Register and test
```python
write_file("/tmp/my_robot_adapter.py", adapter_code)
register_robot_adapter(body_id="my_robot", adapter_py_path="/tmp/my_robot_adapter.py")
install_robot_sdk(body_id="my_robot")
test_robot_adapter(body_id="my_robot", connect_kwargs='{"host": "192.168.1.100"}')
```

### Step 5 — Save as skill
After a successful test:
```python
save_robot_skill(
    name="SDK Integration: my_robot",
    description="Adapter and connection procedure for my_robot SDK",
    body_id="my_robot",
    tags="sdk,onboarding"
)
```

## Error Handling
- `ImportError` after `register_robot_adapter` → SDK import name wrong, check `sdk_import_name` property
- `ConnectionStatus(connected=False)` → wrong host/port/interface, check network config
- `NotImplementedError` → fill in the stub methods in the adapter template

## Reference Examples
See `sdk_adapters/examples/` for Unitree G1 and Go2 as reference implementations.
