## Why

当前 `/api_planning` 接口对多模态输入的处理不够明确和优化：
- 视频检测走对话流程，生成不必要的 session 上下文
- 定时任务只返回文字和单条语音，前端定时触发时缺少语音提示
- 语音和文字的处理流程需要明确统一

随着 CareAgent 从测试转向实际使用，需要优化多模态输入的处理规则，提升用户体验。

## What Changes

- **语音输入 (voice)**: ASR 转文字后走对话流程，等同于文字输入，检测定时任务意图
- **视频输入 (video)**: 摔倒检测后使用模板回复 + TTS 语音，不存储 session（独立事件无需上下文）
- **文字输入 (text)**: 检测定时任务后返回双语音（audio_confirm 立即播放 + audio_reminder 定时播放，使用自然表达）
- **图像输入 (image)**: 明确不支持，返回错误提示

## Capabilities

### New Capabilities

- `video-detection-response`: 视频摔倒检测后的模板回复和 TTS 语音生成，不存储 session
- `dual-audio-schedule`: 定时任务双语音返回机制（确认语音 + 提醒语音）
- `natural-reminder-text`: 提醒语音使用自然表达映射（如"该吃药了！"而非"提醒吃药"）

### Modified Capabilities

- `multi-turn-conversation`: 语音输入处理规则明确为 ASR 后等同文字输入
- `chat-service`: /api_planning 路由逻辑调整，视频检测简化，文字输入增强

## Impact

- **修改文件**: 
  - `services/chat-service/main.py` - 调整 /api_planning 路由逻辑
  - `services/chat-service/executor.py` - 简化视频检测流程，增强文字输入的定时任务处理
  - `services/chat-service/modules/speech.py` - 新增 TTS 调用函数
  
- **API 变更**: 
  - `/api_planning` 响应格式变更：
    - 文字/语音: 新增 `audio_confirm` 和 `audio_reminder` 字段
    - 视频: 简化为 `{status, result, response, audio}`，无 session
  - **BREAKING**: 前端需要适配新的响应格式
  
- **前端变更**: 
  - 需要处理双语音响应
  - 定时任务存储 `audio_reminder` 供定时触发时播放
  - 视频检测不再依赖 session
  
- **依赖变更**: 无新增依赖，复用现有 TTS 服务
