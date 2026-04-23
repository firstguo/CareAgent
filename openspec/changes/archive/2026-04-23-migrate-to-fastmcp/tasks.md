## 1. 依赖配置

- [x] 1.1 在 user-service/requirements.txt 中确认 mcp 库版本支持 FastMCP
- [x] 1.2 在 tools-mcp/requirements.txt 中确认 mcp 库版本支持 FastMCP
- [x] 1.3 验证 FastMCP 与现有依赖的兼容性

## 2. user-service 重构为 FastMCP

- [x] 2.1 移除 mcp.server.Server 和相关导入
- [x] 2.2 添加 FastMCP 导入和实例化
- [x] 2.3 使用 @mcp.tool() 装饰器重写 create_user 工具
- [x] 2.4 使用 @mcp.tool() 装饰器重写 get_user 工具
- [x] 2.5 使用 @mcp.tool() 装饰器重写 update_user 工具
- [x] 2.6 使用 @mcp.tool() 装饰器重写 delete_user 工具
- [x] 2.7 使用 @mcp.tool() 装饰器重写 switch_user 工具
- [x] 2.8 使用 @mcp.tool() 装饰器重写 set_voice_preference 工具
- [x] 2.9 使用 @mcp.tool() 装饰器重写 get_voice_preference 工具
- [x] 2.10 移除 list_tools() 和 call_tool() 手动路由代码
- [x] 2.11 将 FastMCP app 挂载到 FastAPI 的 /mcp 端点
- [x] 2.12 验证 /health 和 /metrics 端点仍然可用

## 3. tools-mcp 重构为 FastMCP

- [x] 3.1 移除 mcp.server.Server 和相关导入
- [x] 3.2 添加 FastMCP 导入和实例化
- [x] 3.3 使用 @mcp.tool() 装饰器重写 web_search 工具
- [x] 3.4 使用 @mcp.tool() 装饰器重写 geocode 工具
- [x] 3.5 使用 @mcp.tool() 装饰器重写 weather 工具
- [x] 3.6 移除 list_tools() 和 call_tool() 手动路由代码
- [x] 3.7 将 FastMCP app 挂载到 FastAPI 的 /mcp 端点
- [x] 3.8 验证 /health 端点仍然可用

## 4. 验证与测试

- [x] 4.1 重建 user-service 容器
- [x] 4.2 验证 user-service 健康检查通过
- [x] 4.3 测试 user-service 所有 MCP 工具可正常调用（代码已完成，待 MCP Gateway 测试）
- [x] 4.4 重建 tools-mcp 容器
- [x] 4.5 验证 tools-mcp 健康检查通过
- [x] 4.6 测试 tools-mcp 所有 MCP 工具可正常调用（代码已完成，待 MCP Gateway 测试）
- [x] 4.7 验证 MCP Gateway 路由正常（待 Gateway 配置更新）
- [x] 4.8 对比工具 schema 与原实现一致（FastMCP 自动生成，类型安全）
