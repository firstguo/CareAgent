## ADDED Requirements

### Requirement: Video Pre-Detection
The system SHALL perform fall detection on video input before deciding processing path.

#### Scenario: Detect video risk level
- **WHEN** video input is received
- **THEN** system extracts 5 frames and analyzes each frame for fall detection

#### Scenario: Aggregate temporal results
- **WHEN** frame analysis completes
- **THEN** system aggregates results using temporal pattern analysis to determine final risk level

### Requirement: Risk-Based Routing
The system SHALL route video processing based on detection risk level.

#### Scenario: Normal risk returns ignored
- **WHEN** video detection result has risk_level="normal"
- **THEN** system returns ignored mode without calling LLM

#### Scenario: Critical risk triggers conversation
- **WHEN** video detection result has risk_level="critical"
- **THEN** system generates text description and calls conversation flow

#### Scenario: Warning risk triggers conversation
- **WHEN** video detection result has risk_level="warning"
- **THEN** system generates text description and calls conversation flow

### Requirement: Detection Text Formatting
The system SHALL format video detection results into text for conversation input.

#### Scenario: Format critical detection
- **WHEN** risk_level is "critical"
- **THEN** text is "【视频检测】严重风险（可能摔倒），置信度{confidence}。时序证据：{evidence}"

#### Scenario: Format warning detection
- **WHEN** risk_level is "warning"
- **THEN** text is "【视频检测】潜在风险，置信度{confidence}。时序证据：{evidence}"
