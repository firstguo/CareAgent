## MODIFIED Requirements

### Requirement: 系统必须支持语音识别(ASR)
系统 SHALL 集成阿里云Fun-ASR录音文件识别服务（基于Qwen3基座），将语音音频转换为文本，支持16kHz及以上采样率，支持中文（普通话、四川话、闽南语、吴语、粤语）、英语、日语等30种语言。

#### Scenario: 识别语音
- **WHEN** 调用speech.transcribe并提供WAV格式音频
- **THEN** 系统使用fun-asr模型返回识别的文本内容

#### Scenario: 识别失败
- **WHEN** 音频质量过差或无法识别
- **THEN** 系统返回错误提示，包含具体错误原因

### Requirement: 系统必须支持语音合成(TTS)
系统 SHALL 集成阿里云CosyVoice v3语音合成服务，将文本转换为语音，支持多种音色选择，使用cosyvoice-v3-flash模型。

#### Scenario: 合成语音
- **WHEN** 调用speech.synthesize提供文本和音色ID
- **THEN** 系统使用cosyvoice-v3-flash模型返回Base64编码的WAV音频数据

#### Scenario: 使用指定音色
- **WHEN** 调用speech.synthesize并指定voice_id为longanyang
- **THEN** 系统使用阳光男声合成语音

### Requirement: 系统必须列出可用音色
系统 SHALL 提供可用音色列表，包含音色ID、名称、性别、语言、描述等信息，音色列表基于CosyVoice v3模型。

#### Scenario: 获取音色列表
- **WHEN** 调用speech.list_voices
- **THEN** 系统返回所有可用音色的详细信息，包括longanyang、longxiaoxia、longxiaochun、stella等音色
