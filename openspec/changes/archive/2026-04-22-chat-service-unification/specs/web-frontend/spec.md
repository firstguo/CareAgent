## MODIFIED Requirements

### Requirement: 系统必须支持实时对话显示
系统需要通过轮询Chat Service REST API获取任务状态，显示对话历史，区分用户和AI的消息，支持语音播放。

#### Scenario: 显示对话消息
- **WHEN** AI返回回复
- **THEN** 系统在对话区显示AI消息，并提供播放按钮

#### Scenario: 播放语音回复
- **WHEN** 用户点击消息的播放按钮
- **THEN** 系统播放TTS生成的语音

#### Scenario: 轮询任务状态
- **WHEN** 用户发送消息后
- **THEN** 前端每2-5秒轮询GET /api_task_status/{task_id}，直到状态为completed

## ADDED Requirements

### Requirement: 系统必须调用Chat Service REST API而非MCP工具
前端SHALL通过REST API调用Chat Service，不再通过Gateway调用MCP工具。

#### Scenario: 提交对话任务
- **WHEN** 用户发送语音消息
- **THEN** 前端POST http://chat-service:8007/api_planning，携带audio_data

#### Scenario: 提交多模态任务
- **WHEN** 用户同时发送语音和图片
- **THEN** 前端POST /api_planning，携带audio_data和image_data

### Requirement: 系统必须管理本地定时任务
前端SHALL在localStorage存储定时任务配置，使用JS定时器触发。

#### Scenario: 保存定时任务
- **WHEN** LLM返回should_save_schedule=true
- **THEN** 前端将schedule信息保存到localStorage

#### Scenario: 触发定时任务
- **WHEN** JS定时器检测到任务到达触发时间
- **THEN** 前端POST /api_planning，trigger_type为"scheduled"

## REMOVED Requirements

### Requirement: 系统通过Gateway调用MCP工具
**Reason**: Chat Service改为REST API，不再使用MCP协议
**Migration**: 
- 删除所有gateway.call_tool()调用
- 改为fetch()或requests调用REST API
- 语音发送：从调用speech.transcribe改为POST /api_planning
- 图片分析：从调用vision.analyze改为POST /api_planning
