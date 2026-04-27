---
name: eaib
description: >-
  Orchestrate the Embodied AI Brain (EAIB) system. Trigger when the user wants
  to control a robot, plan a physical task, process sensor data, store robot
  skills, or evaluate the safety of a proposed action. Use phrases like
  "robot task", "move the robot", "process sensor data", "store robot skill",
  "safety check", "what did the robot learn", or "embodied AI".
---

# Embodied AI Brain (EAIB) Skill

## Overview

EAIB models the functional architecture of the human brain as a set of
cooperating sub-agents.  Each module has a focused responsibility:

| Module | Brain analogue | Responsibility |
|---|---|---|
| **eaib-sensory** | Sensory cortex | Perceive and encode environmental input |
| **eaib-motor** | Motor cortex | Translate plans into motor commands |
| **eaib-memory** | Hippocampus | Store and retrieve episodic / semantic memory |
| **eaib-safety** | Amygdala | Enforce safety constraints; issue ALLOW / WARN / HALT |
| **eaib-executive** | Prefrontal cortex | Plan, coordinate, and adapt across sessions |

## Standard Workflow

Use this sequence for any robot task:

```
1. eaib-sensory   → understand the environment
2. eaib-memory    → retrieve relevant past experience
3. eaib-executive → build an action plan
4. eaib-safety    → validate the plan (REQUIRED before any action)
5. eaib-motor     → execute approved actions
6. eaib-memory    → persist the outcome for future sessions
```

### Safety Rule (non-negotiable)

**Always run eaib-safety before eaib-motor.**  Never bypass the safety check,
even for seemingly simple or time-sensitive tasks.

## Usage Examples

### Example 1 — Pick-and-place task

```
User: "Move the red cube from table A to shelf B."

You (agent):
  task("eaib-sensory", "Describe the current positions of the red cube, table A, and shelf B.")
  task("eaib-memory",  "Retrieve any stored skills for pick-and-place operations.")
  task("eaib-executive", "Plan a pick-and-place: red cube from table A to shelf B.")
  task("eaib-safety",  "Evaluate the pick-and-place plan for safety.")
  # Only if eaib-safety returns ALLOW:
  task("eaib-motor",   "Execute the approved pick-and-place plan.")
  task("eaib-memory",  "Store the outcome of this pick-and-place task.")
```

### Example 2 — Skill persistence

```
User: "Remember how to open the lab door and reuse it next time."

You (agent):
  task("eaib-memory", "Store the door-opening procedure as a semantic skill named 'open-lab-door'.")
  # On the next run:
  task("eaib-memory", "Retrieve the skill 'open-lab-door'.")
```

### Example 3 — Safety evaluation only

```
User: "Is it safe to move the arm at 2 m/s?"

You (agent):
  task("eaib-safety", "Evaluate: move arm at 2 m/s. Check velocity limits.")
```

## Self-Configuration

The robot adapts across sessions by:

1. Reading stored preferences and skills from **eaib-memory** before planning.
2. Using **eaib-executive** to adjust the plan based on retrieved context.
3. Writing post-task lessons and updated preferences back to **eaib-memory**.

Safety constraints are hard-coded and cannot be changed by any module.

## Communication Between Robots

When multiple EAIB instances need to coordinate:

1. Each robot writes its status and intent to a shared workspace path
   (e.g. `/mnt/user-data/workspace/eaib-comms/<robot-id>/status.json`).
2. **eaib-executive** reads peer status files before planning to avoid
   conflicting actions.
3. **eaib-safety** checks for inter-robot collision risks as part of
   its standard evaluation.

## Troubleshooting

| Symptom | Module to check | Action |
|---|---|---|
| Plan repeatedly HALTed | eaib-safety | Review violated constraints in safety log |
| Robot misidentifies objects | eaib-sensory | Increase sensor data quality or quantity |
| Skill not found | eaib-memory | Verify the skill was stored with the correct key |
| Execution deviates from plan | eaib-motor | Check motor feedback and re-run eaib-executive |
| Goal not decomposed correctly | eaib-executive | Restate goal more explicitly |

## Success Criteria

A task is complete when:
- [ ] eaib-sensory produced a structured scene description
- [ ] eaib-memory retrieved relevant context (or confirmed no prior experience)
- [ ] eaib-executive produced a numbered action plan
- [ ] eaib-safety returned ALLOW for every action step
- [ ] eaib-motor executed all steps and reported success
- [ ] eaib-memory persisted the outcome and any new skills learned
