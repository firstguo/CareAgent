## Context

当前 user-service 和 tools-mcp 使用 `mcp.server.Server` 手动注册工具，需要：
1. 手动定义 Tool 对象和 inputSchema
2. 在 list_tools() 中返回工具列表
3. 在 call_tool() 中使用 if/elif 路由到具体实现

这种方式代码冗长、容易出错、维护成本高。

FastMCP 提供装饰器驱动的开发体验：
```python
@mcp.tool()
async def create_user(name: str, role: str, age: int = 0):
    """创建新用户"""
    # 自动从函数签名生成 inputSchema
    # 自动注册到工具列表
    # 自动路由调用
```

## Goals / Non-Goals

**Goals:**
- 将两个 MCP 服务迁移到 FastMCP 框架
- 保持所有工具接口完全兼容（名称、参数、返回值）
- 简化代码结构，减少 50%+ 代码量
- 提升代码可读性和可维护性

**Non-Goals:**
- 不改变工具的业务逻辑
- 不修改 MCP 协议端点
- 不影响其他服务（chat-service、gateway 等）
- 不引入破坏性变更

## Decisions

### Decision 1: 使用 FastMCP 的 FastAPI 集成模式

**选择**: 使用 `FastMCP` 类并挂载到现有 FastAPI 应用

**理由**:
- 保留现有 FastAPI 路由（/health、/metrics）
- FastMCP 提供 `mount()` 方法集成到 FastAPI
- 无需改变服务架构

**实现**:
```python
from mcp.server.fastmcp import FastMCP

# 先创建 FastAPI app 并注册路由
app = FastAPI(title="User MCP Server")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 创建 FastMCP 实例
mcp = FastMCP("user-service")

@mcp.tool()
async def create_user(name: str, role: str):
    """创建新用户"""
    ...

# 使用 streamable_http_app 创建 ASGI 应用并挂载
mcp_app = mcp.streamable_http_app()
app.mount("/mcp", mcp_app)
```

**备选方案**:
- 独立 FastMCP 服务器：会丢失 FastAPI 的健康检查等路由

### Decision 2: 保持工具名称使用点号分隔

**选择**: 保持现有工具名称格式（如 `user.create_user`、`tools.web_search`）

**理由**:
- 与现有 MCP Gateway 配置兼容
- 符合命名空间最佳实践
- 避免破坏性变更

**实现**:
```python
@mcp.tool(name="user.create_user")
async def create_user(name: str, role: str, ...):
    """创建新用户"""
```

### Decision 3: 使用 Pydantic 模型定义复杂参数

**选择**: 对于复杂参数（如 health_info、preferences），使用 Pydantic 模型或 dict 类型

**理由**:
- FastMCP 自动从类型注解生成 JSON Schema
- Pydantic 提供自动验证
- 与现有 FastAPI 风格一致

### Decision 4: 保留结构化日志

**选择**: 继续使用 structlog 记录工具调用日志

**理由**:
- 便于调试和监控
- 与现有日志系统一致
- 在装饰器函数中手动记录

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| FastMCP 版本兼容性 | 可能与现有 mcp 库版本冲突 | 使用兼容版本组合，测试验证 |
| 工具参数类型映射 | Python 类型到 JSON Schema 的映射可能不完全一致 | 手动测试生成的 schema，必要时使用 Field() 注解 |
| MCP 协议端点行为变化 | FastMCP 的端点处理可能与原实现不同 | 对比测试端点响应，确保兼容 |
| 错误处理差异 | FastMCP 的错误处理方式可能不同 | 测试错误场景，确保返回格式一致 |

## Migration Plan

### 部署步骤
1. 更新 user-service 为 FastMCP 实现
2. 更新 tools-mcp 为 FastMCP 实现
3. 逐个服务重建和测试
4. 验证所有工具接口兼容
5. 验证 MCP Gateway 路由正常

### 回滚策略
- 保留旧版代码在 Git 历史中
- 如发现兼容性问题，恢复旧版代码
- 工具接口不变，回滚对客户端透明

### 验证清单
- [ ] user-service 所有工具可正常调用
- [ ] tools-mcp 所有工具可正常调用
- [ ] MCP Gateway 路由正常
- [ ] 工具参数 schema 与原实现一致
- [ ] 错误处理行为一致

## Open Questions

无。所有设计决策已明确。
