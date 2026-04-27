# OpenEAIB — 具身智脑 Embodied AI Brain (EAIB) Development Plan

**Version**: 1.0  
**Date**: 2026-04-28  
**Target Journals**: TRO / Science Robotics  
**Repository**: https://github.com/DaojiePENG/openeaib  
**Base Framework**: DeerFlow (ByteDance)

---

## 1. Project Vision

EAIB is an Embodied AI Brain (具身智脑) that:

- Knows its current computational resources (GPU/CPU/RAM) and connected hardware
- Self-configures any peripheral given only a natural-language notification from the user
- Writes, tests, and persists code as *skills* — callable on-demand by name
- Distinguishes between universal skills and body-specific skills (e.g., Unitree G1 vs Go2)
- Transfers skills across robot bodies intelligently
- Communicates with peer robots to share and request skills
- Enforces safety constraints before executing any physical action
- Learns continuously — unsuccessful or redundant skills are archived automatically

---

## 2. Architecture: Brain-Inspired Modular Multi-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│              前额叶皮层  Prefrontal Cortex                    │
│          (make_eaib_agent — lead orchestrator)               │
│  User ↔ Intent Understanding ↔ Task Planning ↔ Routing      │
└───────┬───────────────────────────────────────────┬──────────┘
        │ middleware chain                           │ subagents
        ▼                                            ▼
┌───────────────┐  ┌──────────────┐  ┌────────────────────────┐
│   岛叶皮层    │  │   杏仁核     │  │     运动皮层            │
│  Insular      │  │  Amygdala    │  │   Motor Cortex          │
│  Cortex       │  │  Safety      │  │   Subagent              │
│  Body Self-   │  │  Constraint  │  │   code-gen + SDK call   │
│  Awareness    │  │  Middleware  │  │   + execution + debug   │
└───────────────┘  └──────────────┘  └────────────────────────┘
        │                                            │
        ▼                                            ▼
┌───────────────┐  ┌──────────────┐  ┌────────────────────────┐
│   小脑        │  │   海马体     │  │   顶叶&枕叶            │
│  Cerebellum   │  │  Hippocampus │  │  Parietal & Occipital  │
│  Skill        │  │  Long-term   │  │  Perception Subagent   │
│  Registry +   │  │  Memory +    │  │  camera / lidar / IMU  │
│  Archiver     │  │  Skill Learn │  │  face recognition      │
└───────────────┘  └──────────────┘  └────────────────────────┘
```

---

## 3. Module Mapping (Neural → Engineering)

| Brain Module | Python Module | Key Responsibility |
|---|---|---|
| 前额叶皮层 Prefrontal Cortex | `eaib/agents/eaib_agent.py` | Lead agent, intent, planning, routing |
| 岛叶皮层 Insular Cortex | `eaib/body/` + `eaib/middlewares/body_awareness_middleware.py` | Body self-awareness, hardware scan |
| 杏仁核 Amygdala | `eaib/amygdala/` + `eaib/middlewares/safety_constraint_middleware.py` | Safety rules, risk assessment, forced clarification |
| 小脑 Cerebellum | `eaib/cerebellum/` + `eaib/middlewares/skill_injection_middleware.py` | Skill CRUD, retrieval, archiving |
| 海马体 Hippocampus | `eaib/hippocampus/` | Long-term memory, skill consolidation |
| 运动皮层 Motor Cortex | `eaib/motor_cortex/` | Code gen, SDK adapters, actuator tools |
| 顶叶&枕叶 Parietal+Occipital | `eaib/occipital_parietal/` | Vision, sensor reading, face recognition |
| 沟通 Communication | `eaib/communication/` | Peer robot skill sharing |

---

## 4. Implementation Phases

### Phase 0 — Foundation ✅
- [x] `backend/packages/harness/deerflow/eaib/` package skeleton (all sub-packages)
- [x] `EAIBState(ThreadState)` — extended state schema
- [x] `EAIBConfig` Pydantic model
- [x] `config.example.yaml` — `eaib:` section
- [x] `langgraph.json` — `eaib_agent` graph entry
- [x] Plan document (this file)

### Phase 1 — 岛叶皮层: Body Self-Awareness ✅
- [x] `BodyProfile` dataclass — body identity + sensor manifest
- [x] `BodyRegistry` — JSON-persisted CRUD for body archives
- [x] `HardwareScanner` — auto-detect /dev/video*, /dev/ttyUSB*, GPU, ROS2 nodes
- [x] `BodyAwarenessMiddleware` — inject body context into agent state each turn

### Phase 2 — 杏仁核: Amygdala Safety System ✅
- [x] `SafetyRules` — structured risk rule library for robotic actions
- [x] `RiskAssessor` — LLM + rule dual-path evaluation
- [x] `SafetyConstraintMiddleware` — intercept dangerous commands, trigger clarification

### Phase 3 — 小脑: Cerebellum Skill System ✅
- [x] `RobotSkill` dataclass — body_id, status (draft/tested/stable/archived)
- [x] `SkillRegistry` — CRUD, body-filtered retrieval, similarity search
- [x] `SkillConsolidation` — draft→tested→stable state machine
- [x] `SkillArchiver` — move redundant/failed skills to archive
- [x] `SkillInjectionMiddleware` — inject matched skills into system prompt
- [x] `skills/robot/universal/` — universal robot skills
- [x] `skills/robot/body_specific/` — body-specific skill templates

### Phase 4 — 海马体: Hippocampus Long-term Memory ✅
- [x] `RobotMemoryStorage` — extends `FileMemoryStorage` with robot fields
- [x] `LearningPipeline` — skill event listener → consolidation trigger

### Phase 5 — 运动皮层: Motor Cortex ✅
- [x] Sensor tools: `read_camera_frame`, `read_imu`, `read_odometry`, `list_sensors`
- [x] Actuator tools: `send_joint_command`, `send_velocity_command`, `emergency_stop`
- [x] ROS tools: `ros_topic_list`, `ros_topic_echo`, `ros_service_call`, `ros_launch`
- [x] SDK adapter base class + Unitree G1/Go2 adapters
- [x] `motor-cortex` subagent registration

### Phase 6 — 顶叶&枕叶: Perception ✅
- [x] `capture_frame` tool (OpenCV)
- [x] `FaceRecognizer` — detection + user identity binding
- [x] `SensorReader` — generic ROS2 topic / direct-driver reader
- [x] `perception` subagent

### Phase 7 — 前额叶皮层: Prefrontal Cortex Lead Agent ✅
- [x] `make_eaib_agent()` factory
- [x] EAIB system prompt builder
- [x] LangGraph graph registration

### Phase 8 — Robot-to-Robot Communication ✅
- [x] `SkillServer` — FastAPI sub-app exposing skill sharing endpoints
- [x] `SkillClient` — pull skills from peer robots

### Phase 9 — Gateway API Extensions ✅
- [x] `/api/eaib/body/` routes
- [x] `/api/eaib/skills/` routes
- [x] `/api/eaib/hardware/` routes

### Phase 10 — Skills Library ✅
- [x] `skills/robot/universal/` — hardware-detection, sdk-integration, code-debug-loop
- [x] `skills/robot/body_specific/template/embodied-locomotion/` — template for any new body
- [x] `skills/robot/body_specific/unitree_g1/embodied-locomotion/SKILL.md`
- [x] `skills/robot/body_specific/unitree_go2/embodied-locomotion/SKILL.md`

### Phase 11 — Tests ✅
- [x] Unit tests: body_registry, hardware_scanner, skill_registry, risk_assessor, adapter_registry
- [x] Integration test: make_eaib_agent smoke test (`test_eaib_agent.py`)

### Phase 12 — Frontend Integration ✅
- [x] `frontend/src/core/eaib/` — TypeScript types, REST API client, React Query hooks
- [x] `frontend/src/components/workspace/robot/` — BodyCard, SkillCard, RobotDashboard
- [x] `frontend/src/app/workspace/robot/page.tsx` — Robot dashboard page
- [x] Sidebar nav entry "Robot" in `workspace-nav-chat-list.tsx`

---

## 5. Key Design Decisions

1. **Zero core modifications**: All EAIB code lives under `deerflow/eaib/` and new gateway routers. DeerFlow's core packages are untouched.
2. **File-based storage**: `body_registry.json` + `robot_memory.json` under `~/.local/share/eaib/`. No extra DB dependency.
3. **Skill format compatibility**: Robot skills use the same SKILL.md + YAML frontmatter format as DeerFlow skills, extended with `body_id` / `status` / `tested_at` fields.
4. **Safety mechanism**: MEDIUM+ risk → calls existing `ask_clarification_tool` → triggers LangGraph `interrupt()`. No new interrupt mechanism needed.
5. **Soft-first principle**: All modules run in pure-software mode on a plain Linux host. Hardware migration = deploying to new body + conversational adaptation.
6. **ROS2 preferred, direct SDK fallback**: Sensor/actuator tools try ROS2 first; fall back to direct SDK when ROS2 is absent.
7. **Face recognition opt-in**: Disabled by default (`eaib.perception.face_recognition.enabled: false`) for privacy compliance.

---

## 6. Directory Structure

```
backend/packages/harness/deerflow/eaib/
├── __init__.py
├── state/
│   ├── __init__.py
│   └── eaib_state.py               # EAIBState(ThreadState)
├── body/                           # 岛叶皮层
│   ├── __init__.py
│   ├── body_profile.py
│   ├── body_registry.py
│   └── hardware_scanner.py
├── amygdala/                       # 杏仁核
│   ├── __init__.py
│   ├── safety_rules.py
│   └── risk_assessor.py
├── cerebellum/                     # 小脑
│   ├── __init__.py
│   ├── skill_types.py
│   ├── skill_registry.py
│   ├── skill_consolidation.py
│   └── skill_archiver.py
├── hippocampus/                    # 海马体
│   ├── __init__.py
│   ├── robot_memory_storage.py
│   └── learning_pipeline.py
├── motor_cortex/                   # 运动皮层
│   ├── __init__.py
│   ├── motor_subagent.py
│   └── sdk_adapters/
│       ├── __init__.py
│       ├── base_adapter.py
│       ├── unitree_g1.py
│       └── unitree_go2.py
├── occipital_parietal/             # 顶叶&枕叶
│   ├── __init__.py
│   ├── camera_tool.py
│   ├── face_recognizer.py
│   └── sensor_reader.py
├── communication/                  # 机器人间通信
│   ├── __init__.py
│   ├── skill_server.py
│   └── skill_client.py
├── tools/                          # EAIB-specific tool groups
│   ├── __init__.py
│   ├── sensor_tools.py
│   ├── actuator_tools.py
│   └── ros_tools.py
├── middlewares/                    # EAIB middlewares
│   ├── __init__.py
│   ├── body_awareness_middleware.py
│   ├── safety_constraint_middleware.py
│   └── skill_injection_middleware.py
└── agents/                         # 前额叶皮层
    ├── __init__.py
    ├── eaib_agent.py
    └── eaib_prompt.py

backend/packages/harness/deerflow/config/
└── eaib_config.py

backend/app/gateway/routers/
├── eaib_body.py
└── eaib_skills.py

skills/robot/
├── universal/
│   ├── hardware-detection/SKILL.md
│   ├── sdk-integration/SKILL.md
│   └── code-debug-loop/SKILL.md
└── body_specific/
    ├── unitree_g1/embodied-locomotion/SKILL.md
    └── unitree_go2/embodied-locomotion/SKILL.md

backend/tests/eaib/
├── __init__.py
├── test_body_registry.py
├── test_hardware_scanner.py
├── test_skill_registry.py
├── test_risk_assessor.py
└── test_eaib_agent.py
```

---

## 7. Deployment Flow

### First deployment on new robot
```bash
git clone https://github.com/DaojiePENG/openeaib.git
cd openeaib && make install
make dev   # starts EAIB agent (eaib_agent graph)
# Open chat → EAIB auto-scans hardware and reports findings
# Tell it: "I connected a Unitree G1 robot"
# → EAIB guides user through SDK install, writes & tests control code,
#   persists skill with body_id="unitree_g1"
```

### Body transition (G1 → Go2)
```bash
# Deploy same repo on Go2 host
make dev
# Tell it: "I swapped the robot body to Unitree Go2"
# → EAIB recognizes body change, retains G1 universal skills,
#   begins Go2 skill development automatically
```

### Peer skill sharing
```bash
# On robot A (has skill "wave_hand"):
# User: "Share the wave_hand skill with robot B at 192.168.1.5"
# → EAIB calls skill_server, robot B receives and imports skill

# On robot B:
# User: "Do you know how to wave hand?"
# → EAIB checks skill registry → found (transferred from A) → executes
```
