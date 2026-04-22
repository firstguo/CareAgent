## ADDED Requirements

### Requirement: 系统必须支持视频危险检测
系统SHALL接收Base64编码的视频数据，解码后抽帧分析，返回包含时序证据的检测结果。

#### Scenario: 视频摔倒检测
- **WHEN** 调用vision.detect_danger_video并提供包含摔倒的视频
- **THEN** 系统返回risk_level为critical，包含temporal_evidence和frame_analysis字段

#### Scenario: 视频正常场景检测
- **WHEN** 调用vision.detect_danger_video并提供正常活动视频
- **THEN** 系统返回risk_level为normal，confidence大于0.9
