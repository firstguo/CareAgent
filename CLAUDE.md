# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

CareAgent 是一个智能看护助手，基于 AI 的多模态交互系统，通过语音、文本、视频帮助用户照顾老年人和小朋友。

## 技术栈

- **后端**: FastAPI + Python 3.11
- **LLM**: LangChain + 通义千问 (DashScope)
- **语音**: 阿里云 DashScope (ASR/TTS)
- **视觉**: Qwen-VL (视频摔倒检测)
- **向量数据库**: Milvus + Mem0 (记忆存储)
- **任务存储**: MongoDB (任务状态、会话管理)
- **缓存**: Redis
- **工具服务**: MCP Gateway + MCP tools/call 协议
- **前端**: Streamlit + JavaScript (localStorage 定时任务)
- **监控**: Prometheus + Grafana

## 服务架构

| 服务 | 端口 | 描述 |
|------|------|------|
| **chat-service** | 8007 | 核心服务（语音+视觉+LLM+记忆+意图识别） |
| **user-service** | 8001 | 用户管理 MCP 服务 |
| **tools-mcp** | 8008 | 工具服务（Web搜索+地址查询） |
| **gateway** | 4444 | MCP 网关 |
| **frontend** | 8501 | Streamlit Web 前端 |

基础设施：MongoDB (27017)、Milvus (19530)、Redis (6379)

## 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看特定服务日志
docker-compose logs -f chat-service

# 健康检查
bash scripts/health-check.sh

# 本地运行 chat-service（开发模式）
cd services/chat-service
uvicorn main:app --reload --port 8007

# 构建单个服务
docker-compose build chat-service
```

## 代码架构

### Chat Service 核心流程

`services/chat-service/main.py` 是 FastAPI 应用入口，提供两个主要同步端点：

1. **对话端点** (`handle_conversation`)：处理文本/语音输入 → ASR 转写 → 会话管理 → LLM 回复 → TTS 合成
2. **视频端点** (`handle_video_input`)：视频预检测 → 风险分流（正常返回 ignored / 危险走对话流程）
3. **异步任务端点** (`/api_planning` 异步路径)：提交任务 → MongoDB 存储 → `execute_task_async` 后台执行

`services/chat-service/executor.py` 包含所有执行逻辑：
- `execute_conversation()` — 多轮对话主入口，包含复杂度检测（`detect_task_complexity`）
- `execute_simple_conversation()` — 单任务快速路径（直接 LLM 回复）
- `execute_complex_task()` — 多任务完整路径（工具调用 + 记忆检索 + 多步骤执行）
- `execute_task_with_complexity_detection()` — 带意图识别和工具缓存的完整执行流程
- `execute_chat_flow()` — 传统五阶段流程（输入→记忆→规划→生成→存储）
- `execute_fall_detection()` — 摔倒检测流程

### 能力模块 (`services/chat-service/modules/`)

- `llm.py` — LLM 服务（通义千问），提供 `llm_plus`、`generate_plan`、`generate_chat_response`、`extract_schedule_intent`
- `speech.py` — 语音服务（ASR 转写 + TTS 合成），提供 `transcribe()`、`synthesize()`
- `vision.py` — 视觉服务，提供 `detect_danger_video()`
- `memory.py` — 记忆服务，提供 `retrieve_memories()`、`store_memory()`、`search_memory()`
- `session.py` — 会话管理，`SessionManager` 类（MongoDB 存储）
- `intent_recognition.py` — 意图识别模块（`IntentRecognizer`、`ParameterExtractor`、`TaskDecomposer`、`LoopValidator`）
- `tool_cache.py` — 工具缓存（从 MCP Gateway 定期刷新可用工具列表）

### 任务复杂度分流

系统根据用户消息自动判断任务复杂度：
- **单任务**（问候、简单问答）→ `execute_simple_conversation()`，不调用工具，直接 LLM 回复
- **多任务**（需要查询外部信息）→ `execute_complex_task()`，工具调用 + 记忆检索

### 工具调用机制

工具通过 MCP Gateway 调用（JSON-RPC 协议）：
- 工具白名单：`{"tools.web_search", "tools.location_query"}`
- 调用流程：intent_recognition → 选择工具 → 通过 `execute_tool_call()` → POST 到 MCP Gateway
- 包含重试机制（tenacity，3次重试）和去重机制

## 添加新功能

### 添加新的任务类型
1. 在 `executor.py` 中添加执行函数
2. 在 `execute_task()` 或 `execute_task_async()` 中根据 `trigger_type`/`event_type` 分发
3. 使用 `@retry` 装饰器为外部 API 调用添加重试

### 添加新的工具
1. 在 `services/tools-mcp/` 中实现工具逻辑
2. 工具会自动注册到 MCP Gateway
3. 更新 `executor.py` 中的 `REGISTERED_TOOLS` 白名单

### 修改对话流程
编辑 `executor.py` 中的 `execute_conversation()`、`execute_simple_conversation()` 或 `execute_complex_task()`。

## 环境配置

复制 `.env.example` 为 `.env` 并配置以下密钥：
- `DASHSCOPE_API_KEY` — 通义千问/语音服务
- `TAVILY_API_KEY` — Web 搜索
- `AMAP_API_KEY` — 高德地图

## 注意事项

- 使用 `asyncio.create_task` 实现异步任务（已替换 Temporal）
- 日志使用 structlog JSON 格式
- 定时任务由前端 JavaScript 管理（`frontend/js/schedule_manager.js`），保存在浏览器 localStorage
- 任务超时：单任务 30s、多任务 120s、视频 180s
- 会话超时：文本 10 分钟、语音 30 分钟
