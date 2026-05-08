## Why

当前 `/api_planning` 接口采用单次请求模式，每次对话独立创建 task_id，无法维护连续的对话上下文。用户在 10 秒内的连续对话被当作独立请求处理，导致：
- 对话历史丢失，LLM 无法理解上下文
- 用户体验割裂，无法进行自然的多轮对话
- 重复从 mem0 检索记忆，增加延迟

随着 CareAgent 从测试阶段转向实际使用，多轮对话成为核心需求。

## What Changes

- **新增会话管理**: 引入 session 概念，10 秒无新消息自动结束会话
- **改造 /api_planning**: 文本/语音输入走同步对话流程，直接返回结果；图像/视频保持异步任务模式
- **双层记忆系统**: session 提供短期对话上下文（最近 10 条消息），mem0 提供长期记忆（用户画像、事实）
- **并发安全**: 使用 MongoDB 原子操作（find_one_and_update）+ 唯一索引 + 重试机制，支持多实例高并发部署
- **新增 MongoDB sessions 集合**: 存储活跃会话状态，TTL 自动清理过期会话

## Capabilities

### New Capabilities

- `session-management`: 会话生命周期管理，包括创建、查找、超时判断、并发安全更新
- `multi-turn-conversation`: 多轮对话流程，双层记忆（session + mem0）上下文构建，同步响应
- `conversation-history`: 对话历史存储与检索，session messages 数组管理

### Modified Capabilities

- `chat-service`: /api_planning 接口行为变更，根据 input.type 区分同步/异步处理路径

## Impact

- **新增文件**: 
  - `services/chat-service/modules/session.py` - 会话管理模块
  - `services/chat-service/main.py` - 修改 /api_planning 路由
  - `services/chat-service/executor.py` - 新增 execute_conversation 函数
  
- **MongoDB 变更**: 
  - 新增 sessions 集合
  - 新增索引：session_key 唯一索引、expire_at TTL 索引
  
- **API 变更**: 
  - `/api_planning` 响应格式变更（文本/语音输入返回 session_id 和 response，而非 task_id）
  - **BREAKING**: 前端需要适配新的响应格式
  
- **依赖变更**: 无新增依赖，复用现有 MongoDB 和 mem0

- **性能影响**: 
  - 文本对话从异步改为同步，响应时间从 60s 降至 5-10s
  - 高并发下原子操作开销 < 50ms
