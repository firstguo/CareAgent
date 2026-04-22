## MODIFIED Requirements

### Requirement: MCP Gateway必须提供统一的服务路由
MCP Gateway需要根据工具名称前缀将请求路由到正确的MCP Server，仅支持user.*路由规则。

#### Scenario: 路由用户服务请求
- **WHEN** 客户端调用user.create_user工具
- **THEN** Gateway将请求路由到User MCP Server (端口8001)

## REMOVED Requirements

### Requirement: Gateway路由speech/vision/llm/memory/schedule服务
**Reason**: 这些服务已合并到chat-service或由前端实现，不再作为独立MCP Server部署
**Migration**: 
- speech.* 工具调用迁移到chat-service内部模块直接调用
- vision.* 工具调用迁移到chat-service内部模块直接调用
- llm.* 工具调用迁移到chat-service内部模块直接调用
- memory.* 工具调用迁移到chat-service内部模块直接调用
- schedule.* 工具调用迁移到前端localStorage和JS定时器
- 前端通过REST API调用chat-service，不再通过Gateway调用这些工具
