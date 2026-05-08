## ADDED Requirements

### Requirement: 系统必须提供统一的任务提交入口
系统SHALL通过 `/api_planning` 接口接收所有类型的任务提交，包括用户主动对话、事件触发（摔倒检测）、定时任务。

#### Scenario: 提交用户主动对话任务
- **WHEN** 客户端提交 `trigger_type: "user_initiated"` 的请求
- **THEN** 系统执行对话流程，返回文本回复和可选的语音回复

#### Scenario: 提交摔倒检测任务
- **WHEN** 客户端提交 `trigger_type: "event_driven"` 且 `event_type: "fall_detection"` 的请求
- **THEN** 系统执行视频摔倒检测，返回风险等级、置信度和时序证据

#### Scenario: 提交定时任务
- **WHEN** 客户端提交 `trigger_type: "scheduled"` 的请求
- **THEN** 系统执行对应的定时任务逻辑

### Requirement: 系统必须在任务输入中支持 event_type 字段
系统SHALL在 `TaskInput` 数据模型中增加可选的 `event_type` 字段，用于区分事件触发类型。

#### Scenario: 摔倒检测请求包含 event_type
- **WHEN** 客户端提交摔倒检测请求
- **THEN** 请求体包含 `event_type: "fall_detection"` 字段

#### Scenario: 用户对话请求不包含 event_type
- **WHEN** 客户端提交用户主动对话请求
- **THEN** 请求体不包含 `event_type` 字段（或为 `null`）

### Requirement: 系统必须删除 /api_event_trigger 接口
系统SHALL移除 `/api_event_trigger` 端点，所有事件触发任务统一通过 `/api_planning` 提交。

#### Scenario: 调用已删除的接口
- **WHEN** 客户端调用 `POST /api_event_trigger`
- **THEN** 系统返回 404 Not Found

#### Scenario: 前端改用统一入口
- **WHEN** 前端需要提交摔倒检测任务
- **THEN** 前端调用 `POST /api_planning`，传入 `trigger_type: "event_driven"` 和视频数据

### Requirement: 系统必须在任务输入中支持视频数据类型
系统SHALL在 `InputData` 模型中支持 `type: "video"` 和 `video_data` 字段。

#### Scenario: 提交视频数据
- **WHEN** 客户端提交视频摔倒检测请求
- **THEN** `input.type` 为 `"video"`，`input.video_data` 为 Base64 编码的视频数据

#### Scenario: 提交文本数据
- **WHEN** 客户端提交文本对话请求
- **THEN** `input.type` 为 `"text"`，`input.text` 为文本内容

## REMOVED Requirements

### Requirement: 系统必须提供独立的事件触发接口
**Reason**: 统一任务入口，减少 API 端点复杂度
**Migration**: 前端改用 `/api_planning` 接口，传入 `trigger_type: "event_driven"`

## MODIFIED Requirements

### Requirement: 系统必须支持视频摔倒检测
**更新说明**: 摔倒检测从独立接口迁移到统一入口，功能逻辑不变

#### Scenario: 检测到摔倒事件
- **WHEN** 通过 `/api_planning` 提交包含摔倒动作的视频（`trigger_type: "event_driven"`, `event_type: "fall_detection"`）
- **THEN** 系统返回 `risk_level` 为 `critical`，`confidence` 大于 0.9，`event_type` 为 `fall_detected`

#### Scenario: 正常活动视频
- **WHEN** 通过 `/api_planning` 提交正常行走视频
- **THEN** 系统返回 `risk_level` 为 `normal`，`event_type` 为 `safe`

#### Scenario: 潜在风险视频
- **WHEN** 通过 `/api_planning` 提交老人缓慢坐下视频
- **THEN** 系统返回 `risk_level` 为 `warning` 或 `normal`，不触发紧急报警
