## ADDED Requirements

### Requirement: MCP Gateway必须提供统一的服务路由
MCP Gateway 需要根据工具名称前缀将请求路由到正确的MCP Server，支持user.*、memory.*、speech.*、vision.*、llm.*、schedule.*六种路由规则。

#### Scenario: 路由用户服务请求
- **WHEN** 客户端调用user.create_user工具
- **THEN** Gateway将请求路由到User MCP Server (端口8001)

#### Scenario: 路由LLM服务请求
- **WHEN** 客户端调用llm.chat工具
- **THEN** Gateway将请求路由到LLM MCP Server (端口8005)

### Requirement: MCP Gateway必须实现JWT认证
MCP Gateway 需要验证所有请求的JWT Token，使用RS256算法验证签名，检查Token有效期和撤销状态。

#### Scenario: 有效Token通过验证
- **WHEN** 请求携带有效的JWT Token
- **THEN** Gateway允许请求通过并转发到目标MCP Server

#### Scenario: 无效Token被拒绝
- **WHEN** 请求携带过期或签名无效的Token
- **THEN** Gateway返回401 Unauthorized错误

#### Scenario: 缺失Token被拒绝
- **WHEN** 请求未携带Authorization头
- **THEN** Gateway返回401 Unauthorized错误

### Requirement: MCP Gateway必须实现速率限制
MCP Gateway 需要对每个用户和全局实施速率限制，使用Redis滑动窗口算法，超限请求返回429错误。

#### Scenario: 用户级别限流
- **WHEN** 用户在1分钟内发起超过30次LLM请求
- **THEN** Gateway返回429 Too Many Requests错误

#### Scenario: 全局限流
- **WHEN** 全局LLM请求在1分钟内超过200次
- **THEN** Gateway返回429 Too Many Requests错误

### Requirement: MCP Gateway必须暴露Prometheus指标
MCP Gateway 需要在/metrics端点提供Prometheus格式的指标数据，包括请求数、延迟、错误率等。

#### Scenario: 获取监控指标
- **WHEN** 访问http://gateway:4444/metrics
- **THEN** 返回Prometheus格式的指标数据
