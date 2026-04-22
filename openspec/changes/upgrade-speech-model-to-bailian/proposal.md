## Why

当前CareAgent语音服务使用的是较旧的`paraformer-v2`（ASR）和`cosyvoice-v1`（TTS）模型。阿里云百炼已推出更新的语音模型：
- **语音识别(ASR)**：`qwen3-asr-flash`系列，基于Qwen3基座，支持更多语言和方言，识别精度显著提升
- **语音合成(TTS)**：`cosyvoice-v3-flash`系列，音质更自然，支持SSML标记语言，首包延迟更低

升级到最新模型可以提升语音交互的准确性和自然度，改善用户体验，同时新模型在性能和成本上更有优势。

## What Changes

- **ASR模型升级**：从`paraformer-v2`升级到`qwen3-asr-flash-filetrans`（录音文件识别）
- **TTS模型升级**：从`cosyvoice-v1`升级到`cosyvoice-v3-flash`
- **SDK更新**：使用`dashscope.audio.tts_v2`新版API（当前使用旧版`tts`）
- **音色列表更新**：更新为CosyVoice v3支持的音色（如`longanyang`等）
- **优化音频处理**：新版SDK支持直接返回二进制音频，简化处理流程

## Capabilities

### New Capabilities
- `qwen3-asr-integration`: 集成Qwen3-ASR-Flash语音识别模型，支持多语言、方言和情感识别
- `cosyvoice-v3-integration`: 集成CosyVoice v3语音合成模型，支持SSML和更低延迟

### Modified Capabilities
- `speech-service`: 升级ASR和TTS模型版本，更新API调用方式，优化音色列表

## Impact

- **受影响代码**：`services/chat-service/modules/speech.py`（核心修改）
- **API变更**：DashScope SDK调用方式从v1升级到v2（`tts_v2`模块）
- **依赖更新**：可能需要更新`dashscope`库版本到最新版
- **音色配置**：音色列表需要更新，部分旧音色可能不再可用
- **向后兼容**：API接口保持不变（`transcribe`、`synthesize`、`list_voices`），对上层调用透明
