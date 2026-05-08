## Context

当前 CareAgent 的 chat-service 采用异步任务模式：
- 所有请求通过 `/api_planning` 提交，创建 task_id
- 后台异步执行（语音识别 → 记忆检索 → LLM 对话 → TTS）
- 前端轮询 `/api_task_status/{task_id}` 获取结果
- 每次请求独立，无会话概念

问题：
- 用户连续对话被当作独立请求，LLM 无法获取上下文
- mem0 的 `get_all()` 返回的是提取的记忆（事实、偏好），而非原始对话历史
- 响应延迟高（60s timeout），不适合简单对话场景

约束：
- 必须向后兼容（图像/视频分析仍走异步流程）
- 支持多实例部署（分布式并发安全）
- 复用现有 MongoDB 和 mem0 基础设施
- 高并发场景（>5 req/s）

## Goals / Non-Goals

**Goals:**
- 实现 10 秒超时自动会话切割
- 提供双层记忆：session（短期）+ mem0（长期）
- 文本/语音对话同步返回（< 15s）
- 并发安全（多实例、高并发）
- 向后兼容（图像/视频保持异步）

**Non-Goals:**
- 流式输出（SSE/WebSocket）- 后续迭代
- 会话持久化超过 10 秒 - 业务需求决定
- 跨设备会话同步 - 单用户单设备场景
- 会话历史导出/搜索 - 仅保留活跃会话

## Decisions

### 1. 会话存储方案：MongoDB sessions 集合

**决策**: 使用 MongoDB 存储会话，而非 Redis 或内存

**理由**:
- 已有 MongoDB 基础设施，零新增依赖
- TTL 索引支持自动清理（虽然精度分钟级，应用层用 last_active 判断 10s）
- 对话量不大（单用户 < 100 msg/day），性能足够
- 支持多实例共享

**替代方案**:
- Redis: 性能更好，天然支持 TTL，但新增依赖
- 内存: 最简单，但多实例不共享，重启丢失

### 2. 并发安全：find_one_and_update + 唯一索引 + 重试

**决策**: 使用 MongoDB 原子操作而非分布式锁

**实现**:
```python
# 原子查找并更新
session = await db.sessions.find_one_and_update(
    {
        "session_key": f"{user_id}:active",
        "last_active": {"$gt": now - 10s}
    },
    {"$set": {"last_active": now}},
    return_document=ReturnDocument.AFTER
)

if not session:
    # 创建新会话（先标记旧会话为 expired）
    await db.sessions.update_many(
        {"session_key": f"{user_id}:active"},
        {"$set": {"status": "expired"}}
    )
    await db.sessions.insert_one(new_session)
```

**理由**:
- MongoDB 原子操作保证并发安全
- 唯一索引防止重复创建
- DuplicateKeyError 时自动重试
- 无额外锁机制，性能更好

**替代方案**:
- 分布式锁（Redis/MongoDB）: 更复杂，锁超时处理困难
- 乐观锁 + 版本号: 高并发下重试风暴

### 3. 双层记忆：session + mem0 结合

**决策**: session 存储原始对话消息，mem0 存储提取的事实和偏好

**上下文构建**:
```
LLM Prompt:
├─ System: 角色设定
├─ Memory (mem0): 用户画像、事实记忆（向量检索）
├─ Session (MongoDB): 最近 10 条对话消息
└─ User: 当前消息
```

**理由**:
- session 提供连续的短期上下文（10s 窗口内的对话）
- mem0 提供长期记忆（用户有高血压、对阿司匹林过敏等）
- 两者互补，避免 token 超限
- mem0 的 `search()` 基于语义相关性，自动筛选最相关的记忆

### 4. API 设计：改造 /api_planning，根据 input.type 分发

**决策**: 在现有 `/api_planning` 路由内部分发，而非新增端点

**逻辑**:
```python
@app.post("/api_planning")
async def api_planning(task_input: TaskInput):
    if task_input.input.type in ["text", "voice"]:
        # 同步对话流程（新）
        return await handle_conversation(task_input)
    else:
        # 异步任务流程（保持）
        return await handle_async_task(task_input)
```

**响应格式**:
- 文本/语音: `{session_id, response, audio_response, is_new_session}`
- 图像/视频: `{task_id, status: "pending"}`

**理由**:
- 向后兼容，前端可逐步迁移
- 单一入口，易于监控
- 避免 API 碎片化

**替代方案**:
- 新增 `/api_chat` 端点: 语义更清晰，但增加路由复杂度

### 5. TTL 设计：应用层 10s + MongoDB 60s 兜底

**决策**: 应用层用 `last_active` 字段判断 10s 超时，MongoDB TTL 索引设为 60s

**理由**:
- MongoDB TTL 索引后台任务每分钟运行一次，精度不够
- 应用层判断精确到毫秒
- TTL 60s 作为兜底，防止异常情况下会话泄漏

**实现**:
```python
# 应用层判断
if session.last_active < now - 10s:
    # 会话已超时，创建新会话
    
# MongoDB 兜底
expire_at = now + 60s  # TTL 索引自动删除
```

### 6. 会话消息限制：最多保留最近 50 条

**决策**: session.messages 数组限制为 50 条，LLM 上下文只取最近 10 条

**理由**:
- 防止 MongoDB 文档过大（> 16MB 限制）
- 10 条消息足够覆盖 10s 窗口内的对话（正常语速 1-2 条/秒）
- 节省 token（10 条消息约 500-1000 tokens）

**实现**:
```python
# 更新时使用 $slice 限制数组大小
{"$push": {"messages": {"$each": [msg], "$slice": -50}}}
```

## Risks / Trade-offs

### 1. MongoDB TTL 精度问题
**风险**: TTL 索引清理延迟，过期会话可能残留 1-2 分钟
**缓解**: 应用层用 `last_active` 判断，TTL 仅作为兜底

### 2. 高并发下 DuplicateKeyError 重试风暴
**风险**: 大量请求同时创建会话，触发重试
**缓解**: 
- 指数退避重试（0.1s, 0.2s, 0.4s）
- 最多重试 3 次
- 实际场景中，10s 窗口内大部分请求复用会话，冲突概率低

### 3. mem0 检索延迟
**风险**: 每次对话调用 `mem0.search()` 增加 200-500ms 延迟
**缓解**:
- mem0 检索与 LLM 调用并行（如果有多个检索源）
- 缓存 mem0 结果（同一用户 1 分钟内相同查询）
- 降低 top_k（从 5 降至 3）

### 4. 前端适配 BREAKING 变更
**风险**: 响应格式变化导致前端解析失败
**缓解**:
- 响应中包含 `mode` 字段（`conversation` vs `task`）
- 前端根据 `mode` 分支处理
- 文档清晰说明变更

### 5. 语音输入超时阈值
**风险**: 语音转文本需要时间，10s 可能不够
**缓解**: 语音输入的超时阈值设为 30s（可配置）

## Migration Plan

### 部署步骤
1. 部署 chat-service 新版本（包含 session 管理）
2. MongoDB 自动创建 sessions 集合和索引（startup 事件）
3. 前端检测响应格式，自动适配（检测 `session_id` vs `task_id`）
4. 监控会话创建频率、超时率、冲突率

### 回滚策略
- 保留原有异步任务逻辑（`handle_async_task`）
- 如会话管理出现问题，可快速回退到旧版本
- sessions 集合数据无需清理（TTL 自动过期）

### 监控指标
- `session_create_count`: 新会话创建数
- `session_reuse_count`: 会话复用数
- `session_timeout_count`: 会话超时数
- `concurrent_conflict_count`: 并发冲突数
- `avg_response_time`: 平均响应时间

## Open Questions

1. **是否需要会话历史查询接口？**
   - 当前设计：会话超时后自动删除
   - 未来可能需要：查询历史对话记录
   - 决策：暂不实现，等待业务需求

2. **多用户共享设备场景？**
   - 当前设计：基于 user_id 管理会话
   - 如果多人使用同一设备，需要切换 user_id
   - 决策：由前端负责 user_id 管理，后端无感知

3. **是否需要对齐 mem0 的 memory 提取时机？**
   - 当前设计：每次对话后调用 `mem0.add()`
   - 可能导致频繁写入
   - 决策：先实现，性能监控后决定是否批量写入
