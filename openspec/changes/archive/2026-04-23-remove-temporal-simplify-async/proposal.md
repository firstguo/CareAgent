## Why

Temporal 工作流引擎虽然提供了强大的任务编排能力（持久化、重试、可视化监控），但对于 CareAgent 当前的使用场景来说过于复杂：

1. **调试困难** - Temporal 的异步执行模型使得本地开发和调试变得复杂，需要启动额外的服务器和 UI
2. **基础设施负担** - 需要维护 Temporal Server、PostgreSQL 元数据库、Temporal UI 三个额外容器，占用约 500MB 内存
3. **过度设计** - 当前任务场景（对话处理、摔倒检测）执行时间短（< 30秒），失败可接受重新提交，不需要 Temporal 提供的强耐久性保证

简化为 asyncio 异步执行可以显著提升开发体验，降低运维成本，同时满足当前业务需求。

## What Changes

- **删除** Temporal 相关基础设施（Server、Worker、Client、PostgreSQL 元数据库）
- **删除** Temporal 代码（workflows/、activities/ 目录）
- **删除** `/api_event_trigger` 接口
- **修改** `/api_planning` 接口，使用 `asyncio.create_task` 替代 Temporal Workflow
- **修改** 摔倒检测功能，从 `/api_event_trigger` 迁移到 `/api_planning` 统一入口（通过 `trigger_type: "event_driven"` 区分）
- **新增** `executor.py` 模块，实现异步任务执行逻辑（替代原 workflows + activities）
- **新增** 简单重试机制（使用 tenacity 库）

## Capabilities

### New Capabilities

- `async-task-execution`: 基于 asyncio 的轻量级异步任务执行系统，支持 fire-and-forget 模式、任务状态跟踪、简单重试
- `unified-task-entry`: 统一的任务入口设计，`/api_planning` 接口通过 `trigger_type` 支持多种触发类型（user_initiated、event_driven、scheduled）

### Modified Capabilities

- `task-orchestration`: 从 Temporal DAG 工作流改为 asyncio 异步执行，移除工作流引擎依赖，简化重试和超时控制
- `video-fall-detection`: 摔倒检测从独立接口 `/api_event_trigger` 合并到 `/api_planning` 统一入口

## Impact

- **服务架构**: 删除 Temporal Server、Temporal UI、PostgreSQL 三个容器，降低部署复杂度
- **依赖变更**: 删除 `temporalio` 依赖，新增 `tenacity` 重试库
- **API 变更**: **BREAKING** - 删除 `/api_event_trigger` 端点，前端需改为调用 `/api_planning`
- **代码结构**: 删除 `workflows/` 和 `activities/` 目录，新增 `executor.py`
- **环境变量**: 删除 `TEMPORAL_*` 相关配置
- **监控变更**: 不再有 Temporal UI (8080端口)，依赖 MongoDB 任务状态查询和日志
