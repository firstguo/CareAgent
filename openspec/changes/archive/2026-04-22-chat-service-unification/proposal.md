## Why

当前CareAgent架构中，speech-service、vision-service、llm-service、memory-service作为4个独立的MCP Server部署，导致：
- 服务间网络调用增加延迟（语音识别→LLM理解→语音合成需要3次HTTP调用）
- 部署运维复杂（8个微服务需要协调管理）
- 上下文共享困难（对话状态需要在多个服务间传递）
- 资源利用不均（各服务独立进程无法共享内存和连接池）

本次整合旨在构建统一的Chat Service作为多模态交互中枢，通过Temporal实现DAG任务编排，简化架构的同时提升性能和可维护性。

## What Changes

- **新增** chat-service (端口8007)，提供纯REST API接口：
  - `POST /api_planning` - 提交任务，异步执行，返回task_id
  - `GET /api_task_status/{task_id}` - 查询任务状态
  
- **合并** 4个独立服务为chat-service内部模块：
  - speech-service → modules/speech.py
  - vision-service → modules/vision.py  
  - llm-service → modules/llm.py
  - memory-service → modules/memory.py

- **新增** Temporal工作流引擎用于DAG任务编排：
  - CareTaskWorkflow定义多步骤执行流程
  - 支持并行执行、条件分支、自动重试
  - Temporal UI提供可视化监控

- **新增** MongoDB用于任务状态持久化：
  - 存储任务执行状态和结果
  - TTL索引自动清理30天前数据

- **变更** 前端定时任务方案：
  - LLM在对话中识别定时任务意图
  - 前端localStorage存储任务配置
  - 前端JS定时器触发（需保持页面打开）
  - 不做PWA

- **删除** 独立部署的5个服务：
  - services/speech-service/
  - services/vision-service/
  - services/llm-service/
  - services/memory-service/
  - services/schedule-service/

- **新增** tools-mcp服务（端口8008），整合外部工具API：
  - TAVILY Web搜索能力
  - AMAP（高德地图）地址查询和路径规划
  - 作为独立MCP Server部署

- **变更** Gateway路由配置：
  - 删除 speech.*、vision.*、llm.*、memory.*、schedule.* 路由
  - 保留 user.* 路由
  - 新增 tools.* 路由 → tools-mcp:8008

- **新增** 基础设施服务：
  - Temporal Server + Temporal UI
  - MongoDB
  - Temporal PostgreSQL元数据库

## Capabilities

### New Capabilities

- `chat-service`: 统一的多模态交互服务，整合语音、视觉、LLM、记忆能力，提供REST API和Temporal工作流编排
- `task-orchestration`: 基于Temporal的DAG任务编排系统，支持多步骤异步执行、状态跟踪、自动重试
- `task-status-tracking`: MongoDB任务状态管理系统，支持任务查询、状态更新、TTL自动清理
- `frontend-schedule-management`: 前端定时任务管理，localStorage存储 + JS定时器触发
- `tools-mcp`: 外部工具整合服务，提供TAVILY Web搜索和AMAP地图查询能力
- `temporal-infrastructure`: Temporal工作流引擎基础设施，包括Server、UI、PostgreSQL元数据库

### Modified Capabilities

- `mcp-gateway`: 路由规则调整，删除speech/vision/llm/memory/schedule路由，保留user路由，新增tools路由
- `web-frontend`: 从MCP工具调用改为REST API调用，新增定时任务本地管理功能

## Impact

- **服务架构**: 从8个微服务调整到5个（chat-service、user-service、tools-mcp、gateway、frontend）
- **API变更**: Chat Service采用REST API而非MCP协议，前端调用方式完全改变
- **新增依赖**: Temporal SDK、MongoDB驱动 (motor)、PostgreSQL (Temporal元数据)
- **新增基础设施**: Temporal Server集群、MongoDB数据库
- **部署变更**: docker-compose.yml需添加Temporal、MongoDB、tools-mcp服务，删除5个旧服务
- **前端变更**: 需实现localStorage定时任务管理、JS定时器、任务状态轮询
- **监控变更**: Temporal UI (8080端口)提供工作流可视化
