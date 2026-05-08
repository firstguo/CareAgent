## Why

当前 `/api_planning` 接口在处理任务时缺少对任务复杂度的智能判定和工具调用的优化：
- 无法区分单任务与多任务场景，导致资源分配不合理
- 任务处理过程中没有通过 MCP Gateway 判定是否需要调用外部 tools
- 多任务处理时缺乏重复调用检测，可能造成资源浪费和冗余操作

随着 CareAgent 功能日益复杂，需要优化 `/api_planning` 接口的任务调度逻辑，提升系统效率和响应质量。

## What Changes

- **任务类型判定**: 在任务处理初期智能识别是单任务还是多任务场景
- **MCP Gateway 工具调用判定**: 在任务处理过程中通过 MCP Gateway 判定是否需要调用外部 tools（如 web_search、location_query）
- **重复调用检测**: 在多任务处理过程中检测并避免重复的工具调用或相同操作
- **执行路径优化**: 根据任务复杂度动态调整执行策略，单任务快速执行，多任务并行/去重处理

## Capabilities

### New Capabilities
- `task-complexity-detection`: 任务复杂度检测，区分单任务与多任务场景
- `mcp-gateway-tool-detection`: MCP Gateway 工具调用判定机制
- `duplicate-call-prevention`: 多任务重复调用检测与预防

### Modified Capabilities
- `chat-service`: /api_planning 接口任务处理逻辑优化，增加任务类型判定、工具调用检测和去重机制
- `task-orchestration`: 任务编排逻辑优化，支持多任务并行处理和重复检测

## Impact

- **修改文件**: 
  - `services/chat-service/main.py` - 调整 /api_planning 路由逻辑
  - `services/chat-service/executor.py` - 增强任务执行逻辑，添加任务类型判定、工具调用检测和去重机制
  
- **API 变更**: 
  - `/api_planning` 请求处理逻辑变更，内部增加任务复杂度分析
  - 响应格式可能增加任务类型标识字段
  
- **性能优化**: 
  - 减少不必要的工具调用，降低外部 API 调用成本
  - 多任务场景下避免重复操作，提升执行效率
  
- **依赖变更**: 无新增外部依赖，复用现有 MCP Gateway 配置
