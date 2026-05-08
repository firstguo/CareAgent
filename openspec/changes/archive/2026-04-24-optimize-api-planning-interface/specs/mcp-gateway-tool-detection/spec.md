## ADDED Requirements

### Requirement: 系统必须在任务规划阶段判定是否需要调用 MCP Gateway 工具
系统SHALL在 `generate_plan` 函数中，让 LLM 判定是否需要调用外部 tools（通过 MCP Gateway），并返回工具调用列表。

#### Scenario: 判定需要调用 web_search
- **WHEN** 用户询问"今天有什么重要新闻？"
- **THEN** LLM 返回的 plan 中包含 `tools: [{"name": "tools.web_search", "args": {"query": "今日重要新闻"}}]`

#### Scenario: 判定需要调用 location_query
- **WHEN** 用户询问"附近有哪些药店？"
- **THEN** LLM 返回的 plan 中包含 `tools: [{"name": "tools.location_query", "args": {"location": "药店", "city": "当前城市"}}]`

#### Scenario: 判定不需要调用工具
- **WHEN** 用户询问"你好，今天过得怎么样？"
- **THEN** LLM 返回的 plan 中 `tools` 为空列表或不存在

### Requirement: 工具调用判定必须返回结构化的工具调用信息
系统SHALL在 plan 中返回每个工具的名称和参数，供后续执行使用。

#### Scenario: 返回单个工具调用
- **WHEN** 只需要调用一个工具
- **THEN** plan.tools 包含一个工具对象，格式为 `{"name": "tools.xxx", "args": {...}}`

#### Scenario: 返回多个工具调用
- **WHEN** 需要调用多个工具
- **THEN** plan.tools 包含多个工具对象，按执行顺序排列

### Requirement: 工具调用判定必须与 MCP Gateway 路由配置兼容
系统SHALL只返回 MCP Gateway 配置中已注册的工具名称（如 `tools.web_search`、`tools.location_query`）。

#### Scenario: 使用已注册的工具名称
- **WHEN** LLM 判定需要搜索功能
- **THEN** 返回的工具名称为 `tools.web_search`（与 gateway-config.json 中的路由匹配）

#### Scenario: 不使用未注册的工具名称
- **WHEN** LLM 判定需要某个未注册的工具
- **THEN** 系统记录警告日志，不使用该工具或返回错误
