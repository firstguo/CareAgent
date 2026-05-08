## 1. 视频检测简化

- [x] 1.1 创建视频检测模板回复函数
- [x] 1.2 修改 execute_fall_detection 使用模板回复
- [x] 1.3 添加 TTS 调用生成语音
- [x] 1.4 移除视频检测的 session 存储逻辑
- [x] 1.5 更新响应格式为 {status, result, response, audio}

## 2. 双语音返回机制

- [x] 2.1 修改 handle_conversation 检测定时任务意图
- [x] 2.2 添加 audio_confirm 生成（对话回复的 TTS）
- [x] 2.3 添加 audio_reminder 生成（提醒语音的 TTS）
- [x] 2.4 更新响应格式包含双语音字段
- [x] 2.5 将 audio_reminder 存入 schedule 对象

## 3. 自然表达映射

- [x] 3.1 创建 REMINDER_TEXT_MAP 映射表
- [x] 3.2 实现 get_natural_reminder_text() 函数
- [x] 3.3 在定时任务检测后调用该函数生成提醒文本

## 4. 语音输入明确化

- [x] 4.1 确认 handle_conversation 中语音输入走 ASR → 文字流程
- [x] 4.2 添加日志记录语音转文字的结果

## 5. 图像输入禁用

- [x] 5.1 添加图像输入的明确错误提示
- [x] 5.2 返回 400 错误："图像输入暂不支持"

## 6. TTS 服务优化

- [x] 6.1 确认 speech.py 中有独立的 TTS 调用函数
- [x] 6.2 优化 TTS 调用为异步（避免阻塞）

## 7. 前端适配文档

- [x] 7.1 更新 API 文档说明新的响应格式
- [x] 7.2 添加双语音处理示例代码
- [x] 7.3 添加视频检测响应示例
