## Context

当前 `/api_planning` 接口采用同步处理模式，对所有输入类型（文本、语音、视频）进行统一处理。但在任务执行过程中：
- 没有区分单任务（简单问答）与多任务（需要多个步骤或工具调用）的场景
- 缺乏对 MCP Gateway 中 tools（如 web_search、location_query）调用的智能判定
- 多任务场景下可能存在重复调用相同工具或执行相同操作的情况
- 同步模式导致 HTTP 超时风险，特别是复杂任务场景

现有架构：
- Chat Service 作为统一入口，内部整合了 speech、vision、llm、memory 模块
- tools-mcp 作为独立服务提供外部工具（web_search、location_query）
- MCP Gateway 负责路由 tools.* 请求到 tools-mcp

## Goals / Non-Goals

**Goals:**
- 实现全异步任务执行：所有请求生成 task_id，后台异步执行，前端轮询结果
- 实现任务复杂度智能检测，区分单任务与多任务（简化版，不包含工具列表）
- 实现工具列表动态获取：从 MCP Gateway 获取并缓存，定时刷新
- 在任务执行过程中通过 LLM 判定是否需要调用 MCP Gateway 中的 tools
- 实现多任务场景下的重复调用检测与去重机制
- 实现动态超时策略：根据任务复杂度调整超时时间

**Non-Goals:**
- 不改变现有的 MCP Gateway 路由机制
- 不修改 tools-mcp 的工具实现
- 不引入新的外部依赖
- 不实现任务进度追踪（只返回简单状态）

## Decisions

### Decision 1: 全异步任务执行模式

**选择**: 所有请求都走异步执行，生成 task_id，前端轮询结果

**理由**:
- 避免 HTTP 超时风险（复杂任务可能执行几分钟）
- 用户体验更好：立即返回，可以显示加载状态
- 服务端更稳定：后台任务不受 HTTP 连接影响
- 支持更灵活的任务管理（取消、重试等）

**实现方式**:
```python
@app.post("/api_planning")
async def api_planning(task_input: TaskInput):
    # 1. 生成 task_id
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    
    # 2. 保存任务到 MongoDB
    await mongo_db.tasks.insert_one({
        "_id": task_id,
        "status": "pending",
        ...
    })
    
    # 3. 启动异步任务（不等待）
    asyncio.create_task(execute_task_async(task_id, task_input, mongo_db))
    
    # 4. 立即返回
    return {"task_id": task_id, "status": "pending"}

# 前端轮询（500ms 间隔）
GET /api_task_status/{task_id}
```

**替代方案**:
- 同步执行：简单但有超时风险，不适合复杂任务
- 混合模式（单任务同步、多任务异步）：增加复杂度，不统一

### Decision 2: 简化的任务复杂度判定（不包含工具列表）

**选择**: 任务复杂度判定只返回任务类型和步骤，不包含工具列表

**理由**:
- 简化 LLM prompt，减少 token 消耗
- 职责更清晰：复杂度判定只负责"难不难"，工具选择交给后续步骤
- 判定更快（少了一个输出字段）
- 工具列表从 MCP Gateway 动态获取，更准确

**实现方式**:
```python
async def detect_task_complexity(user_message: str) -> Dict:
    """
    判定任务复杂度（简化版）
    
    Returns:
        {
            "task_type": "single" | "multi",
            "steps": ["step1", "step2", ...]  # 执行步骤
        }
    """
    # LLM prompt 不包含工具列表信息
    # 只返回任务类型和步骤
```

**替代方案**:
- 包含工具列表：增加 prompt 复杂度，且工具列表可能过时

### Decision 3: 工具列表缓存 + 定时刷新

**选择**: 从 MCP Gateway 获取工具列表，缓存 5 分钟，后台定时刷新

**理由**:
- 工具列表通常不会频繁变化
- 减少每次任务的 HTTP 调用（性能优化）
- 定时刷新保证工具列表的实时性（最多 5 分钟延迟）
- 平衡了实时性和性能

**实现方式**:
```python
# 全局缓存
tool_cache = {
    "tools": [],
    "last_updated": 0,
    "refresh_interval": 300  # 5 分钟
}

@app.on_event("startup")
async def startup():
    # 启动时刷新
    await refresh_tool_cache()
    # 后台定时刷新
    asyncio.create_task(periodic_refresh())

async def refresh_tool_cache():
    """从 MCP Gateway 刷新工具列表"""
    # 调用 MCP Gateway 的 tools/list 接口
    # 更新缓存
    tool_cache["tools"] = tools
    tool_cache["last_updated"] = time.time()

async def get_available_tools() -> List[str]:
    """获取可用工具列表（带缓存）"""
    # 如果缓存过期，刷新
    if time.time() - tool_cache["last_updated"] > 300:
        await refresh_tool_cache()
    return tool_cache["tools"]
```

**替代方案**:
- 每次获取：实时性好，但性能差（每次任务多一次 HTTP 调用）
- 启动时获取：性能最好，但工具更新需要重启服务

### Decision 4: 固定 500ms 轮询间隔

**选择**: 前端使用固定 500ms 间隔轮询任务状态

**理由**:
- 实现简单，便于维护
- 500ms 间隔提供接近实时的体验（最多 500ms 延迟）
- 适合快速响应的场景（大部分任务在 30 秒内完成）
- 服务端压力可控（每秒 2 次请求）

**实现方式**:
```javascript
// 前端轮询逻辑（固定 500ms 间隔）
const pollInterval = 500; // 500ms
const maxAttempts = 360;  // 最多轮询 360 次（180秒）

async function pollTaskStatus(taskId) {
    let attempts = 0;
    
    return new Promise((resolve, reject) => {
        const poll = async () => {
            attempts++;
            const data = await fetch(`/api_task_status/${taskId}`);
            
            if (data.status === 'completed') {
                resolve(data.result);
                return;
            }
            
            if (data.status === 'failed') {
                reject(new Error(data.error));
                return;
            }
            
            if (attempts < maxAttempts) {
                setTimeout(poll, pollInterval);
            } else {
                reject(new Error('Task timeout'));
            }
        };
        
        poll();
    });
}
```

**替代方案**:
- 指数退避：更复杂，但长任务时减少服务端压力
- WebSocket：实时性最好，但实现复杂度高

### Decision 5: 动态超时策略

**选择**: 根据任务复杂度动态调整超时时间

**理由**:
- 单任务简单快速，超时时间短（30秒）
- 多任务需要工具调用，超时时间长（120秒）
- 视频检测最耗时，超时时间最长（180秒）
- 避免资源浪费和任务挂起

**实现方式**:
```python
TIMEOUT_CONFIG = {
    "single": 30,    # 单任务：30秒（简单问答）
    "multi": 120,    # 多任务：120秒（需要工具调用）
    "video": 180     # 视频检测：180秒（视频处理最耗时）
}

# 根据任务类型设置超时
timeout = TIMEOUT_CONFIG.get(task_type, 60)  # 默认 60秒

task = asyncio.create_task(
    asyncio.wait_for(
        execute_task_logic(...),
        timeout=timeout
    )
)
```

**替代方案**:
- 固定超时：简单但不灵活，可能导致长任务超时或短任务等待过久

### Decision 6: 使用集合去重 + 执行历史检测重复调用

**选择**: 在多任务执行过程中，维护一个已执行工具的集合，检测重复调用

**理由**:
- 简单高效，O(1) 时间复杂度检测
- 可以检测相同工具+相同参数的重复调用
- 易于实现和维护

**实现方式**:
```python
# 在 executor.py 中
executed_tools = set()

for tool_call in plan.get("tools", []):
    tool_key = f"{tool_call['name']}:{json.dumps(tool_call['args'], sort_keys=True)}"
    
    if tool_key in executed_tools:
        logger.info("duplicate_tool_call_skipped", tool=tool_call['name'])
        continue  # 跳过重复调用
    
    executed_tools.add(tool_key)
    # 执行工具调用
    result = await execute_tool(tool_call)
```

**替代方案**:
- 布隆过滤器: 适用于大规模场景，但有过时风险
- 数据库记录: 持久化但增加复杂度

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM 判定准确率不足 | 可能误判任务类型 | 使用 few-shot prompt 提升准确率，添加fallback机制 |
| 工具调用去重过于激进 | 可能跳过必要的重复调用 | 仅对相同参数的调用去重，不同参数视为不同调用 |
| 500ms 轮询间隔过短 | 服务端压力增加 | 监控服务端性能，必要时调整间隔 |
| 工具缓存过期 | 使用过时工具列表 | 定时刷新，最多 5 分钟延迟 |
| MCP Gateway 工具调用失败 | 任务执行中断 | 添加重试机制和降级策略 |

## Migration Plan

### 部署步骤
1. 实现工具列表缓存和定时刷新机制
2. 修改 `/api_planning` 为异步执行模式
3. 在 `executor.py` 中添加简化的任务复杂度检测函数
4. 修改 `modules/llm.py` 的 `generate_plan` 支持工具调用返回（使用动态工具列表）
5. 在异步任务执行中集成复杂度检测、工具调用和去重逻辑
6. 实现动态超时策略
7. 添加日志记录，监控任务执行情况
8. 更新前端轮询逻辑（500ms 间隔）
9. 测试各种场景，验证异步执行和去重机制

### 回滚策略
- 保留原有的同步执行逻辑作为 fallback
- 通过配置开关控制是否启用异步模式
- 如发现问题，关闭配置即可回滚到同步模式

### 验证清单
- [ ] 异步任务正常执行，前端轮询获取结果
- [ ] 工具列表缓存正常工作，定时刷新
- [ ] 单任务场景快速响应（< 30秒）
- [ ] 多任务场景正确识别并调用工具
- [ ] 重复工具调用被正确检测和跳过
- [ ] 动态超时策略生效
- [ ] MCP Gateway 工具调用成功
- [ ] 日志记录完整，便于调试

## Open Questions

1. **工具调用超时处理**: 如果 MCP Gateway 工具调用超时，是否需要降级处理？
   - 建议：添加超时配置（默认 10 秒），超时后记录日志并继续执行后续步骤

2. **任务复杂度判定的训练数据**: 如何优化 LLM 判定的准确率？
   - 建议：收集实际使用数据，持续优化 prompt

3. **是否需要缓存工具调用结果**: 对于相同参数的工具调用，是否应该缓存结果？
   - 建议：第一阶段不实现缓存，后续根据性能需求决定
