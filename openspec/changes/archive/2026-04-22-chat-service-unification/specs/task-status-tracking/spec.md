## ADDED Requirements

### Requirement: 任务状态必须持久化到MongoDB
系统SHALL在MongoDB中存储每个任务的完整状态，包括输入、执行步骤、结果、时间戳。

#### Scenario: 创建任务记录
- **WHEN** /api_planning接收到新任务
- **THEN** 在MongoDB tasks集合中插入记录，status为pending

#### Scenario: 更新任务状态
- **WHEN** Workflow执行完成
- **THEN** 更新MongoDB中对应task_id的记录，status改为completed，写入result和completed_at

#### Scenario: 查询任务状态
- **WHEN** 客户端GET /api_task_status/{task_id}
- **THEN** 从MongoDB查询并返回任务完整信息

### Requirement: MongoDB任务记录必须包含执行步骤详情
每个任务记录SHALL记录所有执行步骤的状态、输入输出摘要、时间信息。

#### Scenario: 记录步骤执行信息
- **WHEN** Workflow执行speech.transcribe步骤
- **THEN** 在steps数组中添加：{name: "speech_transcribe", status: "completed", duration_ms: 800}

#### Scenario: 记录步骤失败信息
- **WHEN** vision.analyze步骤失败
- **THEN** 在steps数组中添加：{name: "vision_analyze", status: "failed", error: "错误信息"}

### Requirement: MongoDB任务记录必须支持TTL自动清理
系统SHALL为tasks集合设置TTL索引，30天后自动删除过期任务记录。

#### Scenario: 自动清理过期任务
- **WHEN** 任务创建时间超过30天
- **THEN** MongoDB自动删除该任务记录

#### Scenario: 查询最近任务
- **WHEN** 查询user_id=elder_001的最近10个任务
- **THEN** 按created_at降序返回，不包含已清理的过期任务

### Requirement: MongoDB任务索引必须优化查询性能
系统SHALL在tasks集合上创建必要的索引，支持高效查询。

#### Scenario: 按用户查询任务
- **WHEN** 执行查询 {user_id: "elder_001", created_at: -1}
- **THEN** 使用复合索引 {user_id: 1, created_at: -1}

#### Scenario: 按状态查询任务
- **WHEN** 执行查询 {status: "running"}
- **THEN** 使用索引 {status: 1}

### Requirement: 任务数据模型必须包含触发类型
任务记录SHALL区分用户主动发起、定时触发、事件驱动等不同触发类型。

#### Scenario: 记录用户主动发起的任务
- **WHEN** 用户通过语音对话提交请求
- **THEN** 任务记录trigger_type为"user_initiated"

#### Scenario: 记录定时触发的任务
- **WHEN** 前端JS定时器触发定时任务
- **THEN** 任务记录trigger_type为"scheduled"，包含schedule上下文信息
