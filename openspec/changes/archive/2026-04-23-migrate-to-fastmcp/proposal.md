## Why

当前 user-service 和 tools-mcp 使用 `mcp.server.Server` 手动注册工具和路由，代码冗长且维护成本高。每个工具需要手动定义 Tool 对象、编写 inputSchema，并在 call_tool 中使用 if/elif 路由。FastMCP 框架通过装饰器自动从函数签名生成工具定义，可简化代码 50%+，提升可读性和可维护性。

## What Changes

- 将 user-service 的 MCP 实现从 `mcp.server.Server` 迁移到 FastMCP
- 将 tools-mcp 的 MCP 实现从 `mcp.server.Server` 迁移到 FastMCP
- 使用 `@mcp.tool()` 装饰器替代手动工具注册和路由
- 更新依赖配置（添加 fastmcp 包）
- 保持所有 MCP 工具接口不变（工具名称、参数、返回值完全兼容）

## Capabilities

### New Capabilities
- `fastmcp-integration`: FastMCP 框架集成能力，包括装饰器驱动的工具注册、自动 schema 生成、FastAPI 集成

### Modified Capabilities
- `user-management`: user-service 的 MCP 实现方式从手动注册改为 FastMCP 装饰器，工具接口保持不变
- `tools-mcp`: tools-mcp 服务的 MCP 实现方式从手动注册改为 FastMCP 装饰器，工具接口保持不变

## Impact

**受影响的服务**:
- `services/user-service/main.py` - MCP 实现方式重构
- `services/tools-mcp/main.py` - MCP 实现方式重构
- `services/user-service/requirements.txt` - 添加 fastmcp 依赖
- `services/tools-mcp/requirements.txt` - 添加 fastmcp 依赖

**API 影响**:
- **无破坏性变更**：所有 MCP 工具接口保持不变
- 工具名称、参数 schema、返回值格式完全兼容
- MCP 协议端点（`/mcp`）行为不变

**依赖影响**:
- 新增 fastmcp 包（需要确认版本兼容性）
- 保留现有 mcp 包（FastMCP 基于 mcp 库）
- FastAPI、motor 等其他依赖不受影响
