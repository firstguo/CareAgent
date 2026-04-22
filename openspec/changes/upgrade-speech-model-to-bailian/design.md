## Context

当前CareAgent语音服务使用DashScope SDK的旧版API：
- ASR：使用`dashscope.audio.asr.Transcription`调用`paraformer-v2`模型
- TTS：使用`dashscope.audio.tts.SpeechSynthesizer`调用`cosyvoice-v1`模型

阿里云百炼已推出：
- **Qwen3-ASR-Flash**：基于Qwen3基座的语音识别模型，支持中文（普通话、四川话、闽南语、吴语、粤语）、英语、日语等11种语言
- **CosyVoice v3**：第三代语音合成模型，包括`cosyvoice-v3-flash`（快速版）和`cosyvoice-v3-plus`（高质量版）

新版SDK（`dashscope.audio.tts_v2`）采用WebSocket通信，支持流式和非流式调用，音质和性能显著提升。

## Goals / Non-Goals

**Goals:**
- 升级ASR模型到`qwen3-asr-flash-filetrans`，提升识别精度和多语言支持
- 升级TTS模型到`cosyvoice-v3-flash`，提升音质和降低延迟
- 使用新版SDK API（`tts_v2`），简化音频处理流程
- 更新音色列表为CosyVoice v3支持的音色
- 保持API接口向后兼容，对上层调用透明

**Non-Goals:**
- 不实现流式TTS（当前场景不需要实时流式合成）
- 不实现声音复刻/设计功能（超出当前需求范围）
- 不修改上层调用逻辑（保持`transcribe`、`synthesize`、`list_voices`接口不变）

## Decisions

### Decision 1: ASR模型选择
**选择**：`qwen3-asr-flash-filetrans`（录音文件识别）

**理由**：
- 当前架构是接收Base64编码的音频文件，适合录音文件识别场景
- 支持最长12小时录音，具备情感识别与时间戳功能
- 相比实时语音识别，录音文件识别更适合异步处理模式

**替代方案**：
- `qwen3-asr-flash-realtime`：实时流式识别，适合麦克风输入场景，但不适合当前的文件上传模式
- `paraformer-v2`：继续使用旧模型，但性能和精度不如新模型

### Decision 2: TTS模型选择
**选择**：`cosyvoice-v3-flash`

**理由**：
- Flash版本速度快、成本低，适合CareAgent的语音交互场景
- 支持SSML标记语言，为未来扩展留出空间
- 首包延迟低，用户体验更好

**替代方案**：
- `cosyvoice-v3-plus`：质量更高但速度较慢、成本更高，适合对音质要求极高的场景
- `cosyvoice-v2`：过渡版本，不如v3成熟

### Decision 3: SDK调用方式
**选择**：非流式调用（`SpeechSynthesizer.call()`）

**理由**：
- 当前业务场景是完整文本合成，不需要流式输出
- 非流式调用代码简单，易于维护
- 新版SDK的`call()`方法直接返回二进制音频，无需临时文件

**替代方案**：
- 单向流式调用：适合长文本，但增加回调复杂度
- 双向流式调用：适合实时交互，但当前场景不需要

### Decision 4: 音色选择
**选择**：使用CosyVoice v3官方推荐音色

**理由**：
- 新模型音色经过优化，音质更好
- 选择覆盖不同场景的音色（清新、温柔、沉稳等）
- 保留中英文音色支持

**音色列表**：
- `longanyang`：阳光男声（替代`longyunge`）
- `longxiaoxia`：温柔女声（保留）
- `longxiaochun`：清新女声（保留）
- `stella`：英文女声（替代`aisha`）

## Risks / Trade-offs

### Risk 1: SDK版本兼容性
**风险**：新版`tts_v2`模块需要较新版本的DashScope SDK

**缓解措施**：
- 在`requirements.txt`中明确指定`dashscope>=1.23.4`
- 测试环境验证SDK升级不会影响其他功能

### Risk 2: 音色不可用
**风险**：部分旧音色在v3模型中不再支持

**缓解措施**：
- 查阅官方文档确认音色可用性
- 提供音色映射关系，平滑过渡
- 在`list_voices`中明确标注适用的模型版本

### Risk 3: API调用失败
**风险**：新模型API调用方式变化可能导致失败

**缓解措施**：
- 保留完整的错误处理和日志记录
- 添加详细的异常信息，便于排查
- 在测试环境充分验证后再部署

### Trade-off: 功能简化
**权衡**：不实现流式TTS和声音复刻功能

**理由**：当前场景不需要这些高级功能，保持代码简洁更易维护。未来需要时可以扩展。

## Migration Plan

### 部署步骤
1. 更新`requirements.txt`中的`dashscope`版本
2. 修改`speech.py`模块，升级ASR和TTS调用方式
3. 更新音色列表配置
4. 在测试环境验证语音识别和合成功能
5. 部署到生产环境

### 回滚策略
- 保留旧版代码的git分支
- 如遇问题，可快速回滚到`paraformer-v2`和`cosyvoice-v1`
- 监控错误日志，及时发现异常

### 验证清单
- [ ] ASR识别准确率测试（中英文）
- [ ] TTS音质测试（各音色）
- [ ] 异常场景处理（无效音频、空文本等）
- [ ] 性能测试（响应时间）
- [ ] 音色列表接口正常返回

## Open Questions

1. **音色选择是否需要用户调研**：当前使用官方推荐音色，是否需要根据用户反馈调整？
2. **是否需要支持SSML**：CosyVoice v3支持SSML，但是否需要在CareAgent中暴露此功能？
3. **多语言支持范围**：Qwen3-ASR支持11种语言，是否需要全部启用还是仅保留中英文？
