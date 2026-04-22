## ADDED Requirements

### Requirement: 任务编排必须使用Temporal实现DAG工作流
系统SHALL使用Temporal Workflow编排多步骤任务，支持条件执行、并行执行、依赖管理。

#### Scenario: 执行完整多模态任务
- **WHEN** 用户提交包含语音和图像的请求
- **THEN** Workflow依次执行：语音识别→图像分析→记忆检索→LLM规划→对话生成→语音合成→记忆存储

#### Scenario: 条件执行步骤
- **WHEN** 用户仅提交文本请求（无语音、无图像）
- **THEN** Workflow跳过语音识别和图像分析步骤，直接执行LLM规划

#### Scenario: 并行执行独立步骤
- **WHEN** Workflow需要检索历史记忆
- **THEN** 记忆检索与语音识别、图像分析并行执行

### Requirement: Temporal Workflow必须支持自动重试
系统SHALL为每个Activity配置重试策略，LLM和语音服务调用失败时自动重试。

#### Scenario: LLM调用超时重试
- **WHEN** LLM Activity执行超时（15秒）
- **THEN** Temporal自动重试，最多重试2次

#### Scenario: 语音服务调用失败重试
- **WHEN** 阿里云ASR返回错误
- **THEN** Temporal自动重试，最多重试2次，间隔5秒

### Requirement: Temporal Workflow必须支持超时控制
每个Activity SHALL配置start_to_close_timeout，防止单个步骤无限阻塞。

#### Scenario: 语音识别超时
- **WHEN** speech.transcribe Activity执行超过10秒
- **THEN** Activity被标记为失败，Workflow进入错误处理流程

#### Scenario: 图像分析超时
- **WHEN** vision.analyze Activity执行超过30秒
- **THEN** Activity被标记为失败，返回超时错误

### Requirement: 必须实现CareTaskWorkflow定义
系统SHALL实现CareTaskWorkflow类，包含完整的任务规划执行逻辑。

#### Scenario: Workflow接收任务输入
- **WHEN** /api_planning接口接收到TaskInput
- **THEN** 启动CareTaskWorkflow，传入user_id、input数据、trigger_type

#### Scenario: Workflow返回任务结果
- **WHEN** Workflow所有步骤执行完成
- **THEN** 返回TaskResult，包含text_response、audio_response、schedule_action（如有）

### Requirement: 必须实现Temporal Activities
系统SHALL为每个能力模块实现对应的Temporal Activity函数。

#### Scenario: 实现语音识别Activity
- **WHEN** Workflow调用speech_transcribe Activity
- **THEN** 执行modules/speech.py的transcribe函数，返回识别文本

#### Scenario: 实现图像分析Activity
- **WHEN** Workflow调用vision_analyze Activity
- **THEN** 执行modules/vision.py的analyze_image函数，返回分析结果

#### Scenario: 实现LLM规划Activity
- **WHEN** Workflow调用llm_plan_task Activity
- **THEN** 执行modules/llm.py的generate_plan函数，返回任务计划

#### Scenario: 实现语音合成Activity
- **WHEN** Workflow调用speech_synthesize Activity
- **THEN** 执行modules/speech.py的synthesize函数，返回Base64编码音频
