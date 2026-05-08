## ADDED Requirements

### Requirement: 系统必须在任务处理初期判定任务复杂度
系统SHALL在 `execute_conversation` 函数中增加任务复杂度检测步骤，使用 LLM 分析用户消息，判定是单任务还是多任务。

#### Scenario: 判定为单任务
- **WHEN** 用户输入简单问题如"今天天气怎么样？"
- **THEN** 系统返回 `task_type: "single"`，不包含工具调用

#### Scenario: 判定为多任务
- **WHEN** 用户输入复杂请求如"帮我查一下北京的天气，并推荐附近的药店"
- **THEN** 系统返回 `task_type: "multi"`，包含所需工具列表 `["tools.web_search", "tools.location_query"]`

#### Scenario: 判定失败时使用默认值
- **WHEN** LLM 判定失败或返回格式错误
- **THEN** 系统默认使用 `task_type: "single"` 确保任务继续执行

### Requirement: 任务复杂度检测必须返回结构化的工具需求
系统SHALL在复杂度检测结果中返回所需的工具列表和执行步骤。

#### Scenario: 返回工具需求列表
- **WHEN** 检测到多任务
- **THEN** 返回结构化工具列表，包含工具名称和参数

#### Scenario: 返回执行步骤
- **WHEN** 检测到多任务
- **THEN** 返回执行步骤列表，描述任务执行顺序

### Requirement: 任务复杂度检测必须支持快速路径优化
系统SHALL根据任务类型选择不同的执行路径，单任务使用快速路径，多任务使用完整路径。

#### Scenario: 单任务快速路径
- **WHEN** `task_type` 为 "single"
- **THEN** 系统直接调用 LLM 生成回复，跳过工具调用步骤

#### Scenario: 多任务完整路径
- **WHEN** `task_type` 为 "multi"
- **THEN** 系统执行工具调用、结果整合等完整流程
