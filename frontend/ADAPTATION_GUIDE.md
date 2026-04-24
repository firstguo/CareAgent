# 前端适配指南 - 多模态输入优化

## 📋 变更概述

本次更新适配了后端的**多模态输入处理优化**，主要包括：
1. 文本/语音输入改为**同步对话**模式
2. 视频检测使用**模板回复 + TTS 语音**
3. **双语音返回机制**（audio_confirm + audio_reminder）
4. 定时任务支持**自然表达提醒语音**
5. **图像输入禁用**

---

## 🔧 核心变更

### 1. 响应格式变更

#### 文本/语音输入（同步对话）

**旧格式**（异步任务）:
```json
{
  "task_id": "task_abc123",
  "status": "pending"
}
```

**新格式**（同步对话）:
```json
{
  "mode": "conversation",
  "session_id": "sess_user_1234567890",
  "response": "好的，已设置每天早上8点提醒你吃药",
  "audio_confirm": "base64...",
  "audio_reminder": "base64...",
  "is_new_session": true,
  "message_count": 2,
  "schedule": {
    "cron": "0 8 * * *",
    "message": "提醒吃药",
    "type": "medication_reminder",
    "audio_reminder": "base64..."
  }
}
```

#### 视频输入（异步任务）

**旧格式**:
```json
{
  "task_id": "task_abc123",
  "status": "pending"
}
```

**新格式**:
```json
{
  "status": "recorded",
  "result": {
    "risk_level": "safe",
    "confidence": 0.95
  },
  "response": "视频已记录，一切正常",
  "audio": "base64...",
  "alert_triggered": false
}
```

---

## 📝 修改的文件

### 1. `frontend/js/chat_service_client.js`

#### 主要变更：
- ✅ `sendTextMessage()` - 改为直接调用 `/api_planning`，返回同步响应
- ✅ `sendVoiceMessage()` - 改为直接调用 `/api_planning`，返回同步响应
- ✅ `sendVideoMessage()` - **新增**，替代 `sendImageMessage()`
- ✅ `handleConversationResponse()` - **新增**，处理双语音响应
- ❌ `sendImageMessage()` - **删除**（图像输入已禁用）
- ❌ `sendMultimodalMessage()` - **删除**

#### 使用示例：

```javascript
const client = new ChatServiceClient('http://localhost:8007');

// 发送文本消息
const result = await client.sendTextMessage('user_001', '每天早上8点提醒吃药');

// 处理响应
await client.handleConversationResponse(result, {
  onTextResponse: (text) => {
    console.log('AI回复:', text);
    displayText(text);
  },
  onAudioConfirm: (audioBase64) => {
    console.log('播放确认语音');
    client.playBase64Audio(audioBase64);
  },
  onAudioReminder: (audioBase64, schedule) => {
    console.log('存储提醒语音:', schedule);
    scheduleManager.addSchedule(schedule);
  },
  onScheduleDetected: (schedule) => {
    console.log('检测到定时任务:', schedule);
    showScheduleNotification(schedule);
  }
});
```

---

### 2. `frontend/js/schedule_manager.js`

#### 主要变更：
- ✅ `addSchedule()` - 支持 `audio_reminder` 字段
- ✅ `triggerSchedule()` - 触发时播放 `audio_reminder`
- ✅ `playAudioReminder()` - **新增**，播放提醒语音

#### 使用示例：

```javascript
const scheduleManager = new ScheduleManager();

// 添加定时任务（包含 audio_reminder）
const schedule = scheduleManager.addSchedule({
  type: 'medication_reminder',
  cron: '0 8 * * *',
  message: '提醒吃药',
  audio_reminder: 'base64...',  // 从后端响应中获取
  context: {
    user_id: 'user_001'
  }
});

// 定时触发时自动播放 audio_reminder
// 无需手动调用，ScheduleManager 会自动处理
```

---

### 3. `frontend/app.py` (Streamlit)

#### 主要变更：
- ✅ 输入方式：`["文本", "语音", "视频"]`（移除"图像"）
- ✅ 文本输入：适配同步对话响应格式
- ✅ 语音输入：支持文件上传，调用 ASR 转文字
- ✅ 视频检测：显示模板回复和 TTS 语音
- ❌ 图像输入：**删除**（后端已禁用）

#### 响应处理逻辑：

```python
if result.get("mode") == "conversation":
    # 同步对话响应（新格式）
    text_response = result.get("response", "")
    audio_confirm = result.get("audio_confirm")
    audio_reminder = result.get("audio_reminder")
    schedule = result.get("schedule")
    
    # 显示文本
    st.write(text_response)
    
    # 播放确认语音
    if audio_confirm:
        st.audio(base64.b64decode(audio_confirm), format="audio/wav")
    
    # 显示定时任务信息
    if schedule and audio_reminder:
        st.info(f"Cron: {schedule.get('cron')}")
        st.audio(base64.b64decode(audio_reminder), format="audio/wav")
else:
    # 异步任务响应（旧格式，保持兼容）
    task_id = result.get("task_id")
    # ... 轮询逻辑
```

---

## 🎯 关键功能说明

### 1. 双语音机制

**audio_confirm**（确认语音）:
- 用途：立即播放，确认用户的请求已处理
- 示例："好的，已设置每天早上8点提醒你吃药"
- 播放时机：收到响应后立即播放

**audio_reminder**（提醒语音）:
- 用途：定时触发时播放，提醒用户执行任务
- 示例："该吃药了！"（自然表达）
- 存储位置：localStorage（通过 ScheduleManager）
- 播放时机：定时任务触发时自动播放

### 2. 自然表达映射

后端会根据定时任务类型自动生成自然的提醒语音：

| 任务类型 | 原始 message | 自然表达 |
|---------|-------------|---------|
| `medication_reminder` | "提醒吃药" | "该吃药了！" |
| `meal_reminder` | "用餐提醒" | "吃饭时间到了，记得按时用餐" |
| `care_check` | "健康检查" | "该做健康检查了" |
| `custom` | "自定义内容" | "自定义内容"（使用 message 字段） |

### 3. 视频检测简化

视频检测不再存储 session，直接使用模板回复：

| 风险等级 | 模板回复 |
|---------|---------|
| `safe` | "视频已记录，一切正常" |
| `warning` | "检测到潜在风险，请注意安全" |
| `critical` | "检测到摔倒，已通知紧急联系人" |

---

## 🧪 测试清单

### 文本输入测试
- [ ] 发送普通文本，验证同步响应
- [ ] 发送定时任务文本，验证双语音返回
- [ ] 验证 audio_confirm 立即播放
- [ ] 验证 audio_reminder 存储到 localStorage
- [ ] 验证定时触发时播放 audio_reminder

### 语音输入测试
- [ ] 上传语音文件，验证 ASR 转文字
- [ ] 验证转文字后的对话流程与文本输入一致
- [ ] 验证双语音返回

### 视频输入测试
- [ ] 上传视频文件，验证模板回复
- [ ] 验证 TTS 语音生成
- [ ] 验证不存储 session
- [ ] 验证 critical 风险等级触发警报标志

### 图像输入测试
- [ ] 验证图像输入返回 400 错误
- [ ] 验证错误提示："图像输入暂不支持"

---

## 📦 部署步骤

1. **更新前端文件**:
   ```bash
   # 替换以下文件
   frontend/js/chat_service_client.js
   frontend/js/schedule_manager.js
   frontend/app.py
   ```

2. **重启前端服务**:
   ```bash
   cd frontend
   streamlit run app.py
   ```

3. **验证后端服务**:
   ```bash
   # 确保后端已部署 optimize-multimodal-input-handling 变更
   curl http://localhost:8007/health
   ```

4. **测试端到端流程**:
   ```bash
   # 测试文本输入
   curl -X POST http://localhost:8007/api_planning \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_user",
       "trigger_type": "user_initiated",
       "input": {
         "type": "text",
         "text": "每天早上8点提醒吃药"
       }
     }'
   ```

---

## ⚠️ 注意事项

1. **向后兼容**: 后端保留了异步任务响应格式，旧版前端仍可正常工作
2. **音频播放**: 浏览器需要用户交互后才能自动播放音频
3. **localStorage 限制**: 音频数据较大时可能超出 localStorage 限制（通常 5-10MB）
4. **Session 管理**: 文本/语音输入使用 session（10秒超时），视频检测不使用 session
5. **图像输入**: 已明确禁用，前端不应提供图像上传入口

---

## 🔗 相关文档

- 后端变更: `openspec/changes/optimize-multimodal-input-handling/`
- API 文档: 查看 `frontend/app.py` 中的 API 文档部分
- 自然表达映射: `services/chat-service/executor.py` 中的 `REMINDER_TEXT_MAP`
- 视频检测模板: `services/chat-service/executor.py` 中的 `VIDEO_RESPONSE_TEMPLATES`
