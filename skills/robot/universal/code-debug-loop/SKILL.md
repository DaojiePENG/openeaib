---
name: code-debug-loop
description: >
  Systematic workflow for writing, running, and fixing robot control code
  until it works. Use this whenever developing a new robot skill that involves
  running Python code on hardware or in simulation.
category: robot-universal
---

# Skill: Code-Debug Loop for Robot Skills

## When to Use
- Writing a new robot control script for the first time
- Fixing a script that throws errors or produces wrong behaviour
- Iterating on a skill after initial `save_robot_skill` (DRAFT status)

## Core Principle
**Write → Run → Observe → Fix → Repeat** until success, then save.

## Workflow

### Step 1 — Write the skill function
```python
# Skills must expose a `run(**kwargs) -> dict` entry point
def run(**kwargs) -> dict:
    """Brief description of what this skill does."""
    # ... implementation ...
    return {"status": "ok", "result": ...}
```

Save to: `~/.local/share/eaib/skills/<body_id>/<skill_name>.py`

### Step 2 — Run and capture output
```bash
python -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location('skill', '<path>')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
result = mod.run()
print(result)
"
```

### Step 3 — Diagnose errors

| Error type | Fix |
|---|---|
| `ImportError` | Install missing package; check SDK import name |
| `ConnectionError` / `TimeoutError` | Check robot power, cable, IP address |
| `AttributeError` | Check SDK API version; run `pip show <pkg>` |
| Wrong units / values | Check SDK docs for unit conventions (rad vs deg, m/s vs mm/s) |
| Physical: robot moves wrong | Reduce gains, add delay, verify joint order |

### Step 4 — Promote when working
```python
# Register in Cerebellum
save_robot_skill(name="...", description="...", body_id="...", code_path="<path>")
# Record success to start promotion counter
record_skill_execution(skill_id="<id>", success=True)
```

### Step 5 — After 3 successful runs → STABLE
The registry automatically promotes DRAFT → TESTED → STABLE.
Stable skills are shared with peer robots on request.

## Safety Reminders
- Test with minimal motion (small angles, low velocity) first
- Have `emergency_stop_tool` ready as a quick call
- Always verify physical clearance before any motion command
- Log unexpected sensor values before acting on them
