# OpenEAIB — 具身智脑使用指南

**版本**: 1.0 · **日期**: 2026-04-28  
**仓库**: https://github.com/DaojiePENG/openeaib  
**基础框架**: [DeerFlow 2.0](https://github.com/bytedance/deer-flow)

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [实现内容总览](#3-实现内容总览)
4. [环境准备](#4-环境准备)
5. [快速启动](#5-快速启动)
6. [DeerFlow 基础使用](#6-deerflow-基础使用)
7. [EAIB 扩展使用指南](#7-eaib-扩展使用指南)
   - 7.1 [纯软件模式（无机器人硬件）](#71-纯软件模式无机器人硬件)
   - 7.2 [接入新机器人](#72-接入新机器人)
   - 7.3 [技能系统](#73-技能系统)
   - 7.4 [安全系统](#74-安全系统)
   - 7.5 [机器人间技能共享](#75-机器人间技能共享)
   - 7.6 [面部识别（可选）](#76-面部识别可选)
8. [Robot Dashboard 前端界面](#8-robot-dashboard-前端界面)
9. [REST API 参考](#9-rest-api-参考)
10. [配置参考](#10-配置参考)
11. [开发者指南](#11-开发者指南)
12. [常见问题 FAQ](#12-常见问题-faq)

---

## 1. 项目概述

**EAIB（Embodied AI Brain，具身智脑）** 是在 DeerFlow 框架上构建的机器人 AI 系统，核心目标：

- **零预置知识**：系统启动时不预设任何机器人型号知识，所有硬件适配器通过自然语言对话动态创建
- **自主学习技能**：用户和机器人协作编写控制代码，代码以"技能"形式持久化存储，随调用次数自动升级
- **安全第一**：所有物理操作在执行前经过风险评估，危险操作强制请求用户确认
- **体身无关**：同一套系统可运行在任何机器人机体上，通用技能跨机体共享
- **软件优先**：无需任何机器人硬件即可完整运行，所有功能在纯软件模式下均可测试

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│             前额叶皮层  Prefrontal Cortex                         │
│          make_eaib_agent — 主协调代理 (LangGraph)                 │
│     用户意图理解 ↔ 任务规划 ↔ 子代理路由 ↔ 记忆检索                │
└──────────┬─────────────────────────────────────────┬────────────┘
           │ 中间件链                                 │ 子代理
           ▼                                          ▼
┌──────────────────┐  ┌────────────────┐  ┌──────────────────────┐
│  岛叶皮层         │  │    杏仁核       │  │     运动皮层          │
│  Insular Cortex  │  │   Amygdala     │  │   Motor Cortex       │
│  机体自感知        │  │   安全约束      │  │   代码生成+SDK调用    │
│  BodyRegistry    │  │   RiskAssessor │  │   AdapterRegistry    │
│  HardwareScanner │  │   MEDIUM→确认  │  │   动态适配器          │
└──────────────────┘  │   BLOCKED→拒绝 │  └──────────────────────┘
                      └────────────────┘
┌──────────────────┐  ┌────────────────┐  ┌──────────────────────┐
│    小脑           │  │    海马体       │  │    顶叶&枕叶          │
│  Cerebellum      │  │  Hippocampus   │  │  Occipital-Parietal  │
│  技能注册/检索    │  │  长期记忆       │  │  相机/激光/IMU        │
│  DRAFT→STABLE    │  │  技能巩固       │  │  面部识别             │
│  SkillRegistry   │  │  LearningPipeline│ └──────────────────────┘
└──────────────────┘  └────────────────┘
                      ┌────────────────────────────────┐
                      │    机器人间通信                  │
                      │  SkillServer / SkillClient     │
                      │  /api/eaib/peer/               │
                      └────────────────────────────────┘
```

### 存储位置

| 数据类型 | 路径 |
|---|---|
| 机体档案 | `~/.local/share/eaib/bodies/` |
| 技能元数据 | `~/.local/share/eaib/skills_db/` |
| 技能代码 | `~/.local/share/eaib/skills/` |
| SDK 适配器 | `~/.local/share/eaib/adapters/<body_id>/` |
| 面部数据库 | `~/.local/share/eaib/face_db/` |
| 长期记忆 | `~/.local/share/deerflow/memory/` |

---

## 3. 实现内容总览

### 3.1 后端模块（Python）

```
backend/packages/harness/deerflow/eaib/
├── state/                         # EAIBState(ThreadState) — LangGraph 状态扩展
│   └── eaib_state.py              #   + body_state, skill_context, safety_flags
│
├── body/                          # 岛叶皮层：机体自感知
│   ├── body_profile.py            #   BodyProfile 数据类 + SensorDescriptor
│   ├── body_registry.py           #   JSON 持久化 CRUD（增删改查）
│   └── hardware_scanner.py        #   扫描 /dev/video*, /dev/ttyUSB*, GPU, ROS2
│
├── amygdala/                      # 杏仁核：安全系统
│   ├── safety_rules.py            #   RiskLevel 枚举 + SafetyRule 规则集
│   └── risk_assessor.py           #   正则+谓词双路评估 → RiskAssessment
│
├── cerebellum/                    # 小脑：技能系统
│   ├── skill_types.py             #   RobotSkill 数据类 + SkillStatus 枚举
│   ├── skill_registry.py          #   JSON 持久化 CRUD + 关键词搜索 + 状态机晋升
│   └── skill_archiver.py          #   软删除 + GC
│
├── hippocampus/                   # 海马体：长期记忆
│   ├── robot_memory_storage.py    #   扩展 FileMemoryStorage（机器人专属字段）
│   └── learning_pipeline.py       #   技能生命周期事件 → 巩固触发器
│
├── motor_cortex/                  # 运动皮层：硬件控制
│   ├── motor_subagent.py          #   motor-cortex 子代理配置（30 工具）
│   └── sdk_adapters/
│       ├── base_adapter.py        #   BaseSdkAdapter ABC（接口规范）
│       ├── dynamic_adapter.py     #   DynamicSdkAdapter（运行时 importlib 加载）
│       ├── adapter_registry.py    #   AdapterRegistry（启动时为空，对话中填充）
│       └── examples/              #   参考模板（Unitree G1/Go2，不自动加载）
│
├── occipital_parietal/            # 顶叶&枕叶：感知
│   ├── camera_tool.py             #   OpenCV 相机帧采集
│   ├── face_recognizer.py         #   面部注册/识别（可选 face_recognition 库）
│   └── sensor_reader.py           #   串口/激光/面部工具
│
├── middlewares/                   # EAIB 专属中间件
│   ├── body_awareness_middleware.py    #   每轮注入 body_state
│   ├── safety_constraint_middleware.py #   拦截危险工具调用
│   └── skill_injection_middleware.py   #   每次模型调用前注入技能摘要
│
├── communication/                 # 机器人间通信
│   ├── skill_server.py            #   FastAPI 子应用（技能共享服务端）
│   └── skill_client.py            #   httpx 异步客户端（技能共享客户端）
│
├── tools/                         # 所有 EAIB 工具（33 个）
│   ├── sensor_tools.py            #   list_sensors, read_imu, read_odometry, read_joint_states
│   ├── actuator_tools.py          #   emergency_stop, send_velocity_command, send_joint_command
│   ├── ros_tools.py               #   ros_topic_list/echo, ros_service_call, ros_launch
│   ├── skill_tools.py             #   list/search/save/record/archive robot skills
│   └── adapter_tools.py           #   7 个适配器管理工具（核心硬件接入工具链）
│
└── agents/                        # 前额叶皮层：主代理
    ├── eaib_prompt.py             #   系统提示词构建器（含机体上下文+技能摘要）
    └── eaib_agent.py              #   make_eaib_agent() — LangGraph 工厂函数
```

### 3.2 网关 API（FastAPI）

```
backend/app/gateway/routers/
├── eaib_body.py      # /api/eaib/body/   — 机体管理（列表/当前/注册/扫描/删除）
└── eaib_skills.py    # /api/eaib/skills/ — 技能管理（列表/搜索/创建/归档）

# app.py 挂载点：
#   /api/eaib/peer/  ← skill_server_app（技能共享子应用）
```

### 3.3 前端（TypeScript / Next.js）

```
frontend/src/
├── core/eaib/
│   ├── types.ts    # TypeScript 类型：BodySummary, RobotSkill 等
│   ├── api.ts      # REST fetch 函数（body + skills API）
│   ├── hooks.ts    # React Query hooks：useBodies, useSkills, useHardwareScan 等
│   └── index.ts    # 统一导出
│
├── components/workspace/robot/
│   ├── body-card.tsx        # 机体卡片（设为当前 / 删除）
│   ├── skill-card.tsx       # 技能卡片（状态徽标 / 归档）
│   └── robot-dashboard.tsx  # 机器人仪表盘（机体网格 + 技能列表 + 硬件扫描）
│
└── app/workspace/robot/
    └── page.tsx   # /workspace/robot 路由页面
```

### 3.4 技能库

```
skills/robot/
├── universal/
│   ├── hardware-detection/SKILL.md   # 硬件检测与接入工作流
│   ├── sdk-integration/SKILL.md      # SDK 安装与适配器编写指南
│   └── code-debug-loop/SKILL.md      # 写→运行→观察→修复循环
└── body_specific/
    ├── template/embodied-locomotion/SKILL.md    # 通用运动模板
    ├── unitree_g1/embodied-locomotion/SKILL.md  # G1 专用运动指南
    └── unitree_go2/embodied-locomotion/SKILL.md # Go2 专用运动指南
```

### 3.5 测试

```
backend/tests/eaib/
├── test_body_registry.py    # 机体注册 CRUD + 持久化（9 用例）
├── test_hardware_scanner.py # 硬件扫描输出结构（3 用例）
├── test_skill_registry.py   # 技能 CRUD + 状态机晋升 + 搜索（7 用例）
├── test_risk_assessor.py    # 风险评估规则（7 用例）
├── test_adapter_registry.py # 适配器注册/移除（5 用例）
└── test_eaib_agent.py       # 主代理冒烟测试（5 用例，完全 mock）
```

---

## 4. 环境准备

### 4.1 系统要求

| 依赖 | 最低版本 | 说明 |
|---|---|---|
| Python | 3.12 | 后端运行时 |
| Node.js | 22 | 前端构建 |
| pnpm | 10 | 前端包管理 |
| uv | 最新 | Python 包管理 |
| nginx | 任意 | 本地统一入口 |

### 4.2 安装 uv

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或
pip install uv

# 验证
uv --version
```

### 4.3 克隆仓库

```bash
git clone https://github.com/DaojiePENG/openeaib.git
cd openeaib
```

### 4.4 配置 LLM

```bash
# 从模板创建配置文件（仅首次）
make config

# 编辑 config.yaml，填写 LLM 提供商信息
# 必填：models.default 下的 provider + model + api_key
nano config.yaml
```

最简配置示例（OpenAI）：

```yaml
models:
  default:
    provider: openai
    model: gpt-4o
    api_key: sk-xxxx
```

最简配置示例（本地 Ollama）：

```yaml
models:
  default:
    provider: ollama
    model: qwen2.5:72b
    base_url: http://localhost:11434
```

### 4.5 安装依赖

```bash
make install
# 等价于：
#   cd backend && uv sync
#   cd frontend && pnpm install
```

---

## 5. 快速启动

### 5.1 启动所有服务

```bash
make dev
```

这会同时启动：

| 服务 | 端口 | 说明 |
|---|---|---|
| LangGraph 服务 | 2024 | EAIB / DeerFlow agent 运行时 |
| FastAPI 网关 | 8001 | REST API |
| Next.js 前端 | 3000 | Web UI |
| nginx | 2026 | 统一入口（**访问此地址**） |

打开浏览器：**http://localhost:2026**

### 5.2 查看日志

```bash
# 全部日志
tail -f logs/langgraph.log logs/gateway.log logs/frontend.log

# 仅 EAIB 相关
tail -f logs/langgraph.log | grep -i eaib
```

### 5.3 停止服务

```bash
make stop
```

---

## 6. DeerFlow 基础使用

### 6.1 发起对话

1. 打开 http://localhost:2026
2. 点击左侧 **Chats** → 点击右上角 **New Chat**
3. 在输入框输入任意问题

DeerFlow 的核心能力：
- **深度研究**：自动搜索、总结、生成报告
- **代码执行**：在沙盒中编写并运行 Python 代码
- **工具调用**：支持 Web 搜索、文件读写、MCP 工具等
- **子代理协作**：复杂任务自动分解给专属子代理

### 6.2 使用 EAIB 代理（而非 DeerFlow 默认代理）

当前 LangGraph 中注册了两个图：

| 图 ID | 工厂函数 | 用途 |
|---|---|---|
| `lead_agent` | `deerflow.agents:make_lead_agent` | DeerFlow 默认通用代理 |
| `eaib_agent` | `deerflow.eaib.agents:make_eaib_agent` | 具身智脑机器人代理 |

在 API 调用时指定 `assistant_id` 为 `eaib_agent` 即可使用 EAIB 代理。前端默认调用 `lead_agent`，后续版本将在 UI 中提供选择。

---

## 7. EAIB 扩展使用指南

### 7.1 纯软件模式（无机器人硬件）

EAIB 默认以 **host** 机体启动，代表运行它的这台计算机本身。所有功能均可在无机器人的情况下测试。

**验证 EAIB 正常运行**：

```bash
# 检查 body API
curl http://localhost:2026/api/eaib/body/current
# 期望响应：{"body_id":"host","display_name":"Host (this computer)","is_current":true,...}

# 检查 skills API
curl http://localhost:2026/api/eaib/skills/
# 期望响应：[]（刚启动无技能）

# 硬件扫描（扫描本机）
curl http://localhost:2026/api/eaib/body/scan
# 响应：{"os":"Linux","cameras":[...],"serial_ports":[...],...}
```

**在聊天中与 EAIB 对话**（使用 `eaib_agent` 图时）：

```
用户：你现在的机体是什么？有哪些传感器？
EAIB：当前机体是 "host"，代表这台 Linux 主机。
      检测到传感器：摄像头 x1（/dev/video0）...
```

### 7.2 接入新机器人

> **核心原则**：EAIB 不预置任何机器人型号知识。所有硬件接入通过对话完成。

#### 步骤一：告知系统新机器人

在聊天中输入：

```
用户：我有一台 Unitree Go2 四足机器人，
     SDK 包名是 unitree_sdk2py，
     通过以太网连接，IP 是 192.168.123.161。
     请帮我接入它。
```

EAIB 将自动执行以下流程：

1. **调用 `list_robot_adapters`** — 确认当前无 Go2 适配器
2. **调用 `get_adapter_template`** — 生成适配器代码模板
3. **研究 SDK**（使用 Web 搜索工具）
4. **编写适配器代码**（实现 `connect`, `get_state`, `emergency_stop`）
5. **调用 `register_robot_adapter`** — 保存到 `~/.local/share/eaib/adapters/unitree_go2/`
6. **调用 `install_robot_sdk`** — `pip install unitree_sdk2py`
7. **调用 `test_robot_adapter`** — 验证连接
8. **注册机体档案** — 通过 `/api/eaib/body/register`

#### 步骤二：设置为当前机体

```
用户：请将 Go2 设为当前机体。
```

或通过 API：

```bash
curl -X POST http://localhost:2026/api/eaib/body/current \
  -H "Content-Type: application/json" \
  -d '{"body_id": "unitree_go2"}'
```

#### 步骤三：验证连接

```
用户：读取 Go2 当前状态。
```

EAIB 会调用 `get_state()` 并返回关节位置、电池电量等信息。

#### 手动注册（API 方式）

```bash
# 注册机体
curl -X POST http://localhost:2026/api/eaib/body/register \
  -H "Content-Type: application/json" \
  -d '{
    "body_id": "my_arm_v1",
    "display_name": "My Robot Arm V1",
    "hardware_type": "arm",
    "metadata": {"ip": "192.168.1.100", "dof": 6}
  }'
```

### 7.3 技能系统

#### 技能状态机

```
DRAFT ──(首次成功执行)──► TESTED ──(3次成功)──► STABLE ──(手动)──► ARCHIVED
```

| 状态 | 含义 |
|---|---|
| `draft` | 刚创建，未经测试 |
| `tested` | 至少成功执行 1 次 |
| `stable` | 成功执行 ≥ 3 次（可跨机体共享） |
| `archived` | 软删除，不参与检索 |

#### 通过对话创建技能

```
用户：请帮我写一个让 Go2 向前走 1 米的技能，保存为 "walk_1m"。
```

EAIB 将：
1. 生成 Python 代码（参考 SDK 文档和 `code-debug-loop` skill）
2. 调试直到成功运行
3. 调用 `save_robot_skill` 保存，status=DRAFT

#### 通过 API 查询技能

```bash
# 列出当前机体的所有技能
curl "http://localhost:2026/api/eaib/skills/?body_id=unitree_go2"

# 只看稳定技能
curl "http://localhost:2026/api/eaib/skills/?body_id=unitree_go2&status=stable"

# 搜索
curl "http://localhost:2026/api/eaib/skills/search?q=walk&body_id=unitree_go2"
```

#### 记录执行结果（推动状态晋升）

```bash
# 记录一次成功执行
curl -X POST http://localhost:2026/api/eaib/skills/unitree_go2_walk_1m_abc123/record_execution \
  -H "Content-Type: application/json" \
  -d '{"success": true}'
```

或在聊天中：

```
用户：刚才的 walk_1m 技能执行成功了，请记录。
```

#### 技能代码文件结构

每个技能代码文件（保存在 `~/.local/share/eaib/skills/<body_id>/<name>.py`）必须导出：

```python
def run(**kwargs) -> dict:
    """技能入口点，返回执行结果字典。"""
    # ... 实现 ...
    return {"status": "ok", "result": ...}
```

### 7.4 安全系统

EAIB 的杏仁核模块在每次工具调用前进行风险评估：

| 风险等级 | 触发条件示例 | 系统行为 |
|---|---|---|
| `SAFE` | 读取传感器、列出技能 | 直接执行 |
| `LOW` | 低速运动（< 0.1 m/s） | 直接执行，记录日志 |
| `MEDIUM` | 中等速度运动、ROS 服务调用 | **返回澄清请求，等待用户确认** |
| `HIGH` | 高速运动（> 1 m/s）、未知命令 | **强制请求用户确认** |
| `BLOCKED` | `rm -rf`、`shutdown`、硬件固件刷写 | **永久拒绝，本次会话不可覆盖** |

**示例对话**：

```
用户：让机器人以 2 m/s 的速度向前跑。
EAIB：⚠️ 安全风险评估结果：HIGH
     原因：请求速度 2.0 m/s 超过安全阈值 1.0 m/s
     建议：请先在受控环境测试，降低速度至 0.3 m/s 以内
     请确认：是否继续？（请说明环境和安全措施）
```

### 7.5 机器人间技能共享

EAIB 内置 P2P 技能共享能力，基于 FastAPI 子应用。

#### 作为服务端（暴露本机技能）

技能共享服务默认随网关一起启动，挂载在 `/api/eaib/peer/`：

```bash
# 查看本机可共享的技能
curl http://localhost:2026/api/eaib/peer/skills
```

#### 作为客户端（从对端拉取技能）

在聊天中：

```
用户：机器人 B 在 192.168.1.5 上，请从它那里获取 wave_hand 技能。
```

或通过代码（Python）：

```python
from deerflow.eaib.communication.skill_client import SkillClient
import asyncio

async def pull_skill():
    client = SkillClient(base_url="http://192.168.1.5:8001/api/eaib/peer")
    skills = await client.list_skills()
    wave = next(s for s in skills if s["name"] == "wave_hand")
    await client.push_skill(
        target_url="http://localhost:8001/api/eaib/peer",
        skill_id=wave["skill_id"]
    )

asyncio.run(pull_skill())
```

### 7.6 面部识别（可选）

> 默认关闭，需要显式启用。

#### 启用

在 `config.yaml` 中：

```yaml
eaib:
  perception:
    face_recognition_enabled: true
```

#### 安装可选依赖

```bash
# 高精度模式（推荐）
pip install face_recognition dlib

# 仅有 OpenCV 时自动降级到人脸检测模式（无识别）
```

#### 注册用户面部

```
用户：请注册我的面部，用户名是 daojie。
```

或通过工具调用：

```python
enroll_user_face_tool(user_id="daojie", source="camera")
```

#### 识别用户

```python
identify_user_face_tool(source="camera")
# 返回：{"user_id": "daojie", "confidence": 0.92}
```

---

## 8. Robot Dashboard 前端界面

访问 **http://localhost:2026/workspace/robot** 打开机器人仪表盘。

### 界面功能

#### 机体管理区

- **所有已注册机体**以卡片形式展示
- 当前活跃机体卡片带有 `Active` 蓝色徽标
- 每个卡片显示：机体类型、传感器数量、已安装 SDK 包
- **Set Active** 按钮：切换当前机体
- **删除按钮**：需二次确认，当前活跃机体不可删除
- **Scan Hardware** 按钮：触发硬件扫描，结果展示在页面顶部

#### 技能管理区

- **机体过滤器**：选择查看哪个机体的技能
- **状态过滤器**：Stable / Tested / Draft
- **文本搜索**：实时过滤技能名称、描述、标签
- 每个技能卡片显示：名称、描述、状态徽标、标签、执行统计
- **Archive 按钮**：将技能软删除（状态变为 archived）

---

## 9. REST API 参考

所有 API 基础路径：`http://localhost:2026`

### 机体 API

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/eaib/body/` | 列出所有注册机体 |
| `GET` | `/api/eaib/body/current` | 获取当前活跃机体 |
| `POST` | `/api/eaib/body/current` | 切换当前机体 `{"body_id": "xxx"}` |
| `POST` | `/api/eaib/body/register` | 注册新机体 |
| `GET` | `/api/eaib/body/scan` | 扫描宿主机硬件 |
| `DELETE` | `/api/eaib/body/{body_id}` | 删除机体档案 |

### 技能 API

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/eaib/skills/` | 列出技能（支持 `?body_id=&status=`） |
| `GET` | `/api/eaib/skills/search` | 搜索技能（`?q=walk&body_id=go2`） |
| `GET` | `/api/eaib/skills/{skill_id}` | 获取单个技能 |
| `POST` | `/api/eaib/skills/` | 创建新技能 |
| `DELETE` | `/api/eaib/skills/{skill_id}` | 归档技能 |

### 技能共享 API（Peer）

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/eaib/peer/skills` | 列出本机可共享技能 |
| `GET` | `/api/eaib/peer/skills/{skill_id}` | 获取单个可共享技能详情 |
| `POST` | `/api/eaib/peer/skills/import` | 从对端导入技能 |

---

## 10. 配置参考

`config.yaml` 中 EAIB 相关配置（全部为可选项，有默认值）：

```yaml
eaib:
  body_registry:
    storage_dir: "~/.local/share/eaib/bodies"   # 机体档案存储目录
    default_body_id: "host"                       # 默认机体（纯软件模式）

  skill_registry:
    storage_dir: "~/.local/share/eaib/skills_db" # 技能元数据目录
    stable_threshold: 3                           # TESTED→STABLE 所需成功次数
    skills_code_dir: "~/.local/share/eaib/skills" # 技能代码目录

  safety:
    clarification_threshold: "MEDIUM"            # 触发确认的最低风险等级
    enabled: true                                 # 是否启用安全中间件

  perception:
    face_db_dir: "~/.local/share/eaib/face_db"  # 面部数据库目录
    default_camera_index: 0                       # 默认相机索引

  peer_sharing:
    port: 8001                                    # 技能共享服务监听端口
    allow_imports: true                           # 是否允许接受对端技能
```

---

## 11. 开发者指南

### 11.1 运行测试

```bash
# 需要先安装 uv
pip install uv

# 运行全部测试
cd backend && make test

# 只运行 EAIB 测试
cd backend && uv run pytest tests/eaib/ -v

# 运行单个测试文件
cd backend && uv run pytest tests/eaib/test_body_registry.py -v
```

### 11.2 代码规范检查

```bash
cd backend && make lint   # ruff check

cd frontend && pnpm lint
cd frontend && pnpm typecheck
```

### 11.3 添加新的 SDK 适配器（手动方式）

在 `backend/packages/harness/deerflow/eaib/motor_cortex/sdk_adapters/examples/` 中参考已有模板，创建 `my_robot.py`：

```python
from deerflow.eaib.motor_cortex.sdk_adapters.base_adapter import BaseSdkAdapter, ConnectionStatus

class Adapter(BaseSdkAdapter):
    body_id = "my_robot"
    sdk_package = "my_robot_sdk"
    sdk_import_name = "my_robot_sdk"

    def connect(self, **kwargs) -> ConnectionStatus:
        import my_robot_sdk
        self._client = my_robot_sdk.Client(kwargs.get("host"))
        self._client.connect()
        return ConnectionStatus(connected=True, body_id=self.body_id, message="OK")

    def get_state(self) -> dict:
        return self._client.get_state()

    def emergency_stop(self) -> bool:
        self._client.stop()
        return True
```

然后通过工具注册：

```python
register_robot_adapter_tool(
    body_id="my_robot",
    adapter_py_path="/path/to/my_robot.py",
    notes="手动创建"
)
```

### 11.4 添加新的安全规则

编辑 `backend/packages/harness/deerflow/eaib/amygdala/safety_rules.py`：

```python
SafetyRule(
    rule_id="custom_rule_001",
    description="禁止激光雷达直射人脸",
    risk_level=RiskLevel.BLOCKED,
    patterns=[re.compile(r"lidar.*face|face.*lidar", re.I)],
    advice="激光雷达不得对准人体面部",
),
```

### 11.5 目录结构导览

```
openeaib/
├── Makefile                    # 主命令入口
├── config.yaml                 # 活动配置（gitignore）
├── config.example.yaml         # 配置模板（含 eaib: 章节）
├── backend/
│   ├── langgraph.json          # 注册了 eaib_agent 图
│   ├── app/gateway/            # FastAPI 网关
│   │   └── routers/
│   │       ├── eaib_body.py    # 机体 API
│   │       └── eaib_skills.py  # 技能 API
│   ├── packages/harness/deerflow/
│   │   ├── eaib/               # EAIB 核心模块
│   │   └── config/
│   │       └── eaib_config.py  # EAIBConfig Pydantic 模型
│   └── tests/eaib/             # EAIB 单元/集成测试
├── frontend/
│   └── src/
│       ├── core/eaib/          # TS 类型 + API + hooks
│       ├── components/workspace/robot/ # UI 组件
│       └── app/workspace/robot/       # 仪表盘页面
└── skills/robot/               # 机器人技能库
    ├── universal/              # 通用技能（跨机体）
    └── body_specific/          # 机体专属技能
```

---

## 12. 常见问题 FAQ

**Q: 启动后 `make dev` 报错 `uv not found`**  
A: 需要先安装 uv：`pip install uv` 或 `curl -LsSf https://astral.sh/uv/install.sh | sh`，然后重新打开终端。

**Q: 访问 `/api/eaib/body/current` 返回 404**  
A: 网关服务可能未完全启动，等待约 10 秒后重试。也可检查 `logs/gateway.log`。

**Q: 接入机器人时 EAIB 如何知道 SDK 的用法？**  
A: EAIB 会使用 Web 搜索工具查找 SDK 文档，或要求用户提供文档 URL。如果 SDK 不在 PyPI 上，告知 EAIB GitHub 链接或粘贴 README。

**Q: 可以同时管理多台机器人吗？**  
A: 可以。每台机器人注册一个 body_id，技能和适配器分别存储。任意时刻只有一个 `current_body`，通过 `set_current_body` 切换。

**Q: 技能代码存在安全风险吗？**  
A: 技能代码以 `importlib` 动态加载，在当前进程中执行（无沙盒隔离）。仅在可信环境中使用，不要从不信任来源导入技能。

**Q: 如何彻底重置 EAIB 数据？**  
A: 删除 `~/.local/share/eaib/` 目录下的所有文件，重启服务即可回到初始状态。

**Q: 前端 Robot 页面显示空白**  
A: 确认网关服务正在运行（`curl http://localhost:8001/health`），并检查浏览器控制台是否有网络错误。

**Q: EAIB 和 DeerFlow 默认代理有什么区别？**  
A: DeerFlow `lead_agent` 是通用研究/任务代理；`eaib_agent` 在其基础上添加了三层中间件（机体感知、安全约束、技能注入）和 33 个机器人专属工具，专门面向具身机器人场景。

---

*本文档由 GitHub Copilot 协同 DaojiePENG 生成。如发现错误或需补充，欢迎提交 Pull Request。*
