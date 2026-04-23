## ADDED Requirements

### Requirement: 系统必须支持 FastMCP 框架集成
系统 SHALL 使用 FastMCP 框架实现 MCP 服务，通过装饰器驱动的方式注册工具，自动从函数签名生成工具定义和参数 schema。

#### Scenario: FastMCP 服务初始化
- **WHEN** MCP 服务启动
- **THEN** 系统创建 FastMCP 实例并挂载到 FastAPI 应用的 /mcp 端点

#### Scenario: 工具自动注册
- **WHEN** 使用 @mcp.tool() 装饰器定义函数
- **THEN** 系统自动将函数注册为 MCP 工具，无需手动维护工具列表

### Requirement: 系统必须自动从函数签名生成工具 schema
FastMCP SHALL 从 Python 类型注解自动生成 JSON Schema，包括参数类型、必填字段、默认值和描述信息。

#### Scenario: 基本类型参数生成
- **WHEN** 工具函数包含 str、int、float、bool 类型参数
- **THEN** 系统生成对应的 JSON Schema 类型定义

#### Scenario: 可选参数处理
- **WHEN** 工具函数参数带有默认值或 Optional 类型
- **THEN** 系统在 JSON Schema 中标记为非必填字段

#### Scenario: 复杂类型参数生成
- **WHEN** 工具函数包含 dict 或 Pydantic 模型参数
- **THEN** 系统生成嵌套的 JSON Schema 结构

### Requirement: 系统必须保持 MCP 协议端点兼容
FastMCP 集成的 /mcp 端点 SHALL 完全兼容标准 MCP 协议，支持 tools/list 和 tools/call 方法。

#### Scenario: tools/list 请求
- **WHEN** 客户端发送 tools/list 请求到 /mcp 端点
- **THEN** 系统返回所有使用 @mcp.tool() 注册的工具列表及其 schema

#### Scenario: tools/call 请求
- **WHEN** 客户端发送 tools/call 请求调用指定工具
- **THEN** 系统自动路由到对应的装饰器函数并返回结果

### Requirement: 系统必须保留 FastAPI 自定义路由
使用 FastMCP 集成时，系统 SHALL 保留现有的 FastAPI 路由（如 /health、/metrics），不受 MCP 端点影响。

#### Scenario: 健康检查端点可用
- **WHEN** 客户端访问 /health 端点
- **THEN** 系统返回服务健康状态，与 MCP 端点独立运行

#### Scenario: 指标端点可用
- **WHEN** 客户端访问 /metrics 端点
- **THEN** 系统返回 Prometheus 指标数据
