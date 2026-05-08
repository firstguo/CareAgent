## Context

当前 CareAgent 使用 Temporal 工作流引擎进行任务编排，包括：
- CareTaskWorkflow: 多模态对话任务（语音识别→记忆检索→LLM规划→对话生成→记忆存储）
- VideoFallDetectionWorkflow: 视频摔倒检测任务

这两个 Workflow 通过 `/api_planning` 和 `/api_event_trigger` 两个独立接口触发。

**当前架构痛点：**
1. 本地调试需要启动 Temporal Server + PostgreSQL + Temporal UI 三个容器
2. Temporal 的异步执行模型使得断点调试困难
3. 任务执行时间短（< 30秒），不需要 Temporal 的持久化保证
4. 两个独立接口增加了前端调用复杂度

**约束条件：**
- 保持现有的 MongoDB 任务状态存储
- 保持现有的 modules/ 模块（speech, vision, llm, memory）
- 前端已有轮询机制（`/api_task_status`），无需修改

## Goals / Non-Goals

**Goals:**
- 移除 Temporal 依赖，简化为 asyncio 异步执行
- 统一任务入口，`/api_planning` 支持所有触发类型
- 保持任务状态跟踪能力（pending → running → completed/failed）
- 实现简单重试机制（针对外部 API 调用）
- 降低部署复杂度（删除 3 个容器）

**Non-Goals:**
- 不实现任务持久化（进程重启会丢失正在执行的任务，可接受）
- 不实现复杂的 DAG 编排（当前任务流程是线性的）
- 不实现可视化监控（依赖日志和 MongoDB 状态查询）
- 不改变前端轮询机制

## Decisions

### Decision 1: 使用 asyncio.create_task 替代 Temporal

**选择**: `asyncio.create_task()` + fire-and-forget 模式

**理由**:
- 简单直观，调试友好
- 无需额外基础设施
- 适合短时间任务（< 30秒）
- FastAPI 原生支持

**替代方案**:
- Celery + Redis: 过于复杂，增加 Redis 依赖
- 同步执行: 用户体验差，阻塞 HTTP 响应

**实现方式**:
```python
@app.post("/api_planning")
async def api_planning(task_input: TaskInput):
    task_id = generate_id()
    await save_task(task_id, "pending")
    
    # Fire-and-forget: 后台执行，不等待结果
    asyncio.create_task(execute_task(task_id, task_input))
    
    return {"task_id": task_id, "status": "pending"}
```

### Decision 2: 统一任务入口，删除 `/api_event_trigger`

**选择**: 在 `/api_planning` 中通过 `trigger_type` 区分任务类型

**理由**:
- 减少 API 端点，简化前端调用
- 统一的认证、限流、日志逻辑
- 摔倒检测本质上也是一种任务触发

**实现方式**:
```python
# 前端调用摔倒检测
POST /api_planning
{
    "user_id": "user_001",
    "trigger_type": "event_driven",
    "event_type": "fall_detection",
    "input": {
        "type": "video",
        "video_data": "base64..."
    }
}
```

### Decision 3: 使用 tenacity 实现重试

**选择**: tenacity 库（声明式重试）

**理由**:
- 语法简洁，`@retry` 装饰器即可
- 支持指数退避、最大重试次数
- 比手动重试代码更清晰

**替代方案**:
- 手动重试循环: 代码冗长，容易出错
- 不重试: 外部 API 调用失败率较高，不可接受

**实现方式**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def call_llm_with_retry(prompt):
    return await llm.generate(prompt)
```

### Decision 4: 任务执行器放在 executor.py

**选择**: 新增 `executor.py` 模块，替代 `workflows/` + `activities/`

**理由**:
- 清晰的职责分离：main.py 负责 API，executor.py 负责业务逻辑
- 避免 main.py 过于臃肿
- 方便单元测试

**目录结构**:
```
chat-service/
├── main.py          # FastAPI 应用 + API 端点
├── executor.py      # 任务执行逻辑（替代 workflows + activities）
└── modules/         # 能力模块（保持不变）
```

### Decision 5: 超时控制使用 asyncio.wait_for

**选择**: `asyncio.wait_for()` 包装整个任务执行

**理由**:
- Python 标准库，无需额外依赖
- 简单易用

**实现方式**:
```python
async def execute_task_with_timeout(task_id, task_input, timeout=60):
    try:
        await asyncio.wait_for(
            execute_task(task_id, task_input),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        await update_task(task_id, "failed", error="Task timeout")
```

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| **进程重启丢失任务** | 正在执行的任务会中断 | 任务执行时间短（< 30秒），发生概率低；用户可重新提交 |
| **没有可视化监控** | 无法实时查看任务执行进度 | 依赖 MongoDB 状态查询 + 日志；未来可添加简单的 Web UI |
| **重试逻辑不如 Temporal 强大** | 不支持复杂的重试策略 | 当前场景简单重试足够；复杂场景可后续引入 tenacity 高级配置 |
| **并发任务过多可能导致资源耗尽** | 大量并发任务占用内存 | 添加并发限制（asyncio.Semaphore）；监控内存使用 |
| **前端需要修改调用方式** | `/api_event_trigger` 被删除 | 前端改动小：只需修改 URL 和添加 `trigger_type` 字段 |

## Migration Plan

### 部署步骤

1. **代码修改**
   - 删除 `workflows/` 和 `activities/` 目录
   - 新增 `executor.py`
   - 修改 `main.py`（移除 Temporal，修改 `/api_planning`，删除 `/api_event_trigger`）
   - 修改 `requirements.txt`（删除 temporalio，新增 tenacity）
   - 修改前端 `app.py`（摔倒检测改为调用 `/api_planning`）

2. **Docker 配置更新**
   - `docker-compose.yml`: 删除 temporal、temporal-ui、temporal-postgresql 服务
   - `.env`: 删除 `TEMPORAL_*` 环境变量

3. **部署验证**
   - 测试 `/api_planning` 正常对话流程
   - 测试 `/api_planning` 摔倒检测流程
   - 测试 `/api_task_status` 状态查询
   - 验证重试机制（模拟 API 失败）

### 回滚策略

如果出现问题，可以：
1. 回滚到上一个 Docker 镜像版本
2. Temporal 相关代码保留在 Git 历史中，可随时恢复

## Open Questions

无（所有设计决策已明确）
