## 1. 依赖更新

- [x] 1.1 检查当前dashscope库版本
- [x] 1.2 更新requirements.txt，指定dashscope>=1.23.4
- [x] 1.3 在测试环境安装新依赖并验证导入正常

## 2. ASR模型升级

- [x] 2.1 修改transcribe函数，将模型从paraformer-v2改为qwen3-asr-flash-filetrans
- [x] 2.2 更新Transcription调用参数，适配新模型API
- [x] 2.3 优化临时文件处理逻辑（如新SDK支持直接传入音频数据）
- [x] 2.4 更新错误处理，适配新模型的错误码和消息格式
- [x] 2.5 添加多语言识别支持的日志记录

## 3. TTS模型升级

- [x] 3.1 更新import语句，从dashscope.audio.tts改为dashscope.audio.tts_v2
- [x] 3.2 修改synthesize函数，使用新版SpeechSynthesizer类
- [x] 3.3 将模型从cosyvoice-v1改为cosyvoice-v3-flash
- [x] 3.4 更新调用方式，使用新的call()方法（非流式）
- [x] 3.5 移除临时文件处理逻辑（新SDK直接返回二进制音频）
- [x] 3.6 更新错误处理，适配新SDK的异常类型

## 4. 音色列表更新

- [x] 4.1 更新VOICE_LIST常量，替换为CosyVoice v3支持的音色
- [x] 4.2 添加longanyang（阳光男声）音色
- [x] 4.3 保留longxiaoxia、longxiaochun等可用音色
- [x] 4.4 替换aisha为stella（英文女声）
- [x] 4.5 更新音色描述信息，标注适用场景

## 5. 代码优化与清理

- [x] 5.1 移除不再使用的import语句
- [x] 5.2 更新模块文档字符串，反映新模型版本
- [x] 5.3 优化日志记录，添加模型版本信息
- [x] 5.4 检查并更新函数注释中的参数说明
- [x] 5.5 确保get_aliyun_token函数正常工作

## 6. 测试验证

- [x] 6.1 测试ASR中文语音识别功能
- [x] 6.2 测试ASR英文语音识别功能
- [x] 6.3 测试TTS各音色语音合成功能
- [x] 6.4 测试异常场景（空音频、空文本、无效音色等）
- [x] 6.5 验证list_voices接口返回正确的音色列表
- [x] 6.6 性能测试：对比新旧模型的响应时间

## 7. 文档与部署

- [x] 7.1 更新.env.example，确认DASHSCOPE_API_KEY配置说明
- [x] 7.2 记录音色变更说明（如需要迁移指南）
- [x] 7.3 在测试环境部署并验证
- [x] 7.4 准备回滚方案（保留旧版代码分支）
- [x] 7.5 部署到生产环境并监控错误日志
