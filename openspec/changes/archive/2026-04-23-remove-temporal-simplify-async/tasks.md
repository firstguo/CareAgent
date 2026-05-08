## 1. 准备工作

- [x] 1.1 创建 `executor.py` 模块骨架（包含 `execute_task`、`execute_chat_flow`、`execute_fall_detection` 函数签名）
- [x] 1.2 在 `requirements.txt` 中删除 `temporalio==1.4.0`，新增 `tenacity>=8.2.0`
- [x] 1.3 在 `TaskInput` 模型中新增可选的 `event_type: Optional[str] = None` 字段

## 2. 实现任务执行器 (executor.py)

- [x] 2.1 实现 `execute_task(task_id, task_input)` 主入口函数，根据 `trigger_type` 分发到不同执行逻辑
- [x] 2.2 实现 `execute_chat_flow(task_id, task_input)` 函数（迁移原 CareTaskWorkflow 逻辑）
- [x] 2.3 实现 `execute_fall_detection(task_id, task_input)` 函数（迁移原 VideoFallDetectionWorkflow 逻辑）
- [x] 2.4 实现 `update_task_status(task_id, status, result=None, error=None)` 辅助函数（更新 MongoDB）
- [x] 2.5 为 LLM 调用添加 tenacity 重试装饰器（`@retry(stop=stop_after_attempt(3), wait=wait_exponential(...))`）
- [x] 2.6 为视觉 API 调用添加 tenacity 重试装饰器
- [x] 2.7 在 `execute_task` 中使用 `asyncio.wait_for()` 添加 60 秒超时控制

## 3. 修改 main.py

- [x] 3.1 删除 Temporal 相关导入（`from temporalio.client import Client`、`from temporalio.worker import Worker`）
- [x] 3.2 删除全局变量 `temporal_client`、`temporal_worker`、`worker_task`
- [x] 3.3 删除 `start_temporal_worker()` 函数
- [x] 3.4 修改 `startup()` 函数：移除 `await start_temporal_worker()` 调用
- [x] 3.5 修改 `shutdown()` 函数：移除 Temporal Worker 停止逻辑，新增后台任务取消逻辑
- [x] 3.6 修改 `/health` 端点：移除 `temporal_connected` 字段
- [x] 3.7 修改 `/api_planning` 端点：使用 `asyncio.create_task(execute_task(...))` 替代 `temporal_client.start_workflow()`
- [x] 3.8 删除 `/api_event_trigger` 端点及相关代码
- [x] 3.9 删除 `EventTriggerInput` 数据模型
- [x] 3.10 添加后台任务跟踪列表（`background_tasks: Set[asyncio.Task]`）
- [x] 3.11 在 `shutdown()` 中等待所有后台任务完成（最多 30 秒）

## 4. 删除 Temporal 相关代码

- [x] 4.1 删除 `workflows/` 目录（包含 `care_task_workflow.py`、`__init__.py`）
- [x] 4.2 删除 `activities/` 目录（包含 `task_activities.py`、`__init__.py`）
- [x] 4.3 从 `main.py` 中移除对 workflows 和 activities 的所有引用

## 5. 修改前端

- [x] 5.1 修改 `frontend/app.py` 中的视频摔倒检测功能：将 `POST /api_event_trigger` 改为 `POST /api_planning`
- [x] 5.2 更新请求体：添加 `trigger_type: "event_driven"` 和 `event_type: "fall_detection"` 字段
- [ ] 5.3 测试前端视频上传和结果轮询功能

## 6. 更新 Docker 配置

- [x] 6.1 在 `docker-compose.yml` 中删除 `temporal` 服务
- [x] 6.2 在 `docker-compose.yml` 中删除 `temporal-ui` 服务
- [x] 6.3 在 `docker-compose.yml` 中删除 `temporal-postgresql` 服务
- [x] 6.4 在 `.env` 和 `.env.example` 中删除 `TEMPORAL_*` 相关环境变量
- [ ] 6.5 更新 `services/chat-service/Dockerfile`（如果需要）

## 7. 更新文档

- [x] 7.1 更新 `README.md`：移除 Temporal 相关描述，更新架构图和技术栈
- [x] 7.2 更新 `README.md`：添加 asyncio 异步执行说明
- [ ] 7.3 删除或归档 `openspec/changes/archive/2026-04-22-chat-service-unification/specs/task-orchestration/spec.md` 中的 Temporal 相关内容

## 8. 测试验证

- [ ] 8.1 测试 `/api_planning` 正常对话流程（`trigger_type: "user_initiated"`）
- [ ] 8.2 测试 `/api_planning` 摔倒检测流程（`trigger_type: "event_driven"`）
- [ ] 8.3 测试 `/api_task_status` 状态查询（验证状态转换：pending → running → completed/failed）
- [ ] 8.4 测试任务超时控制（模拟长时间运行的任务）
- [ ] 8.5 测试重试机制（模拟 API 调用失败，验证重试 3 次）
- [ ] 8.6 测试服务关闭时后台任务的处理（发送 SIGTERM 信号）
- [ ] 8.7 验证 Docker Compose 启动时不再包含 Temporal 相关容器
