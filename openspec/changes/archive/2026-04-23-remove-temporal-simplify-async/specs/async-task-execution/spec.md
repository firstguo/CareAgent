## ADDED Requirements

### Requirement: 系统必须支持基于 asyncio 的异步任务执行
系统SHALL使用 `asyncio.create_task()` 实现 fire-and-forget 模式的异步任务执行，替代 Temporal Workflow。

#### Scenario: 提交任务后立即返回
- **WHEN** 客户端调用 `/api_planning` 接口
- **THEN** 系统立即返回 `task_id` 和 `status: "pending"`，不等待任务执行完成

#### Scenario: 后台异步执行任务
- **WHEN** 任务提交成功
- **THEN** 系统通过 `asyncio.create_task()` 在后台启动任务执行

#### Scenario: 任务执行状态更新
- **WHEN** 任务开始执行
- **THEN** 系统将任务状态从 `pending` 更新为 `running`

#### Scenario: 任务执行完成
- **WHEN** 任务成功执行
- **THEN** 系统将任务状态更新为 `completed`，并保存执行结果

#### Scenario: 任务执行失败
- **WHEN** 任务执行过程中抛出异常
- **THEN** 系统将任务状态更新为 `failed`，并记录错误信息

### Requirement: 系统必须支持任务超时控制
系统SHALL使用 `asyncio.wait_for()` 为任务执行设置超时限制，防止任务无限阻塞。

#### Scenario: 任务执行超时
- **WHEN** 任务执行时间超过 60 秒
- **THEN** 系统终止任务执行，将状态更新为 `failed`，错误信息为 "Task timeout"

#### Scenario: 正常任务在超时内完成
- **WHEN** 任务在 60 秒内完成执行
- **THEN** 系统正常处理结果，不触发超时逻辑

### Requirement: 系统必须支持外部 API 调用重试
系统SHALL为 LLM、视觉等外部 API 调用配置自动重试机制，使用 tenacity 库实现。

#### Scenario: LLM 调用失败重试
- **WHEN** LLM API 调用失败
- **THEN** 系统自动重试，最多重试 3 次，使用指数退避策略（2秒、4秒、8秒）

#### Scenario: 视觉分析调用失败重试
- **WHEN** 视觉 API 调用失败
- **THEN** 系统自动重试，最多重试 3 次，使用指数退避策略

#### Scenario: 重试次数用尽后仍然失败
- **WHEN** 重试 3 次后仍然失败
- **THEN** 系统将任务状态更新为 `failed`，记录最后一次错误信息

### Requirement: 系统必须支持多类型任务执行
系统SHALL根据 `trigger_type` 执行不同的任务逻辑（对话流程、摔倒检测等）。

#### Scenario: 执行用户主动对话任务
- **WHEN** `trigger_type` 为 `user_initiated`
- **THEN** 系统执行对话流程：记忆检索 → LLM 规划 → 对话生成 → 记忆存储

#### Scenario: 执行摔倒检测任务
- **WHEN** `trigger_type` 为 `event_driven` 且 `event_type` 为 `fall_detection`
- **THEN** 系统执行摔倒检测流程：视频解码 → 抽帧分析 → 时序推理 → 返回风险等级

### Requirement: 系统必须在进程关闭时优雅处理后台任务
系统SHALL在 FastAPI shutdown 事件中等待正在执行的后台任务完成或取消。

#### Scenario: 服务关闭时有正在执行的任务
- **WHEN** FastAPI 应用接收到 shutdown 信号
- **THEN** 系统等待所有正在执行的后台任务完成（最多等待 30 秒），然后关闭

#### Scenario: 服务关闭时任务未完成
- **WHEN** 后台任务在 30 秒内未完成
- **THEN** 系统取消任务，将状态更新为 `failed`，然后关闭

## REMOVED Requirements

### Requirement: 任务编排必须使用Temporal实现DAG工作流
**Reason**: 使用 asyncio 替代 Temporal，简化架构
**Migration**: 任务编排逻辑迁移至 `executor.py`，使用 `asyncio.create_task()` 执行

### Requirement: Temporal Workflow必须支持自动重试
**Reason**: Temporal 已移除，重试逻辑改为 tenacity 库实现
**Migration**: 使用 `@retry` 装饰器替代 Temporal RetryPolicy

### Requirement: Temporal Workflow必须支持超时控制
**Reason**: Temporal 已移除，超时控制改为 asyncio.wait_for() 实现
**Migration**: 使用 `asyncio.wait_for(task, timeout=60)` 替代 start_to_close_timeout

### Requirement: 必须实现CareTaskWorkflow定义
**Reason**: Temporal Workflow 已移除
**Migration**: 对话流程逻辑迁移至 `executor.py` 的 `execute_chat_flow()` 函数

### Requirement: 必须实现Temporal Activities
**Reason**: Temporal Activities 已移除
**Migration**: Activity 函数逻辑直接调用 `modules/` 中的函数，或迁移至 `executor.py` 的辅助函数
