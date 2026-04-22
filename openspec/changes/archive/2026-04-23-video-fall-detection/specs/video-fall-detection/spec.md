## ADDED Requirements

### Requirement: 系统必须支持视频摔倒检测
系统SHALL接收视频文件，通过抽帧分析和时序推理检测摔倒事件，返回风险等级、置信度和时序证据。

#### Scenario: 检测到摔倒事件
- **WHEN** 调用video.detect_fall并提供包含摔倒动作的视频
- **THEN** 系统返回risk_level为critical，confidence大于0.9，event_type为fall_detected

#### Scenario: 正常活动视频
- **WHEN** 调用video.detect_fall并提供正常行走视频
- **THEN** 系统返回risk_level为normal，event_type为safe

#### Scenario: 潜在风险视频
- **WHEN** 调用video.detect_fall并提供老人缓慢坐下视频
- **THEN** 系统返回risk_level为warning或normal，不触发紧急报警

### Requirement: 系统必须支持视频解码和抽帧
系统SHALL使用OpenCV解码视频文件，均匀抽取5帧用于分析。

#### Scenario: 8秒视频抽帧
- **WHEN** 提供8秒视频文件
- **THEN** 系统均匀抽取5帧，间隔约1.6秒

#### Scenario: 短视频抽帧
- **WHEN** 提供少于5帧的视频
- **THEN** 系统返回所有可用帧，不报错

### Requirement: 系统必须实现时序推理聚合
系统SHALL分析帧序列的风险等级变化模式，识别典型摔倒特征（normal→warning→critical→critical）。

#### Scenario: 典型摔倒模式
- **WHEN** 帧序列为[normal, warning, critical, critical, critical]
- **THEN** 系统判定为摔倒，置信度大于0.9

#### Scenario: 非摔倒模式
- **WHEN** 帧序列为[normal, normal, warning, normal, normal]
- **THEN** 系统判定为normal或warning，不触发critical报警

#### Scenario: 置信度计算
- **WHEN** 5帧中3帧为critical
- **THEN** 系统计算置信度为0.7 + (3/5) * 0.25 = 0.85

### Requirement: 系统必须返回详细检测结果
系统SHALL返回包含风险等级、置信度、时序证据、帧分析详情和建议措施的完整结果。

#### Scenario: 完整结果结构
- **WHEN** 视频分析完成
- **THEN** 返回结果包含risk_level、confidence、event_type、temporal_evidence、frame_analysis、recommendations字段

#### Scenario: 分级建议措施
- **WHEN** risk_level为critical且confidence大于0.9
- **THEN** recommendations包含"立即联系紧急联系人"等紧急建议

- **WHEN** risk_level为normal
- **THEN** recommendations包含"未检测到异常"等正常提示
