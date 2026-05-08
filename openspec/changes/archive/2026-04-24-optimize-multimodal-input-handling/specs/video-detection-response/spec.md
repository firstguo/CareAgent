## ADDED Requirements

### Requirement: Video Detection Template Response
The system SHALL use predefined templates to generate response text for video fall detection results, instead of calling LLM.

#### Scenario: Safe detection response
- **WHEN** video detection result has risk_level="safe"
- **THEN** system uses template "视频已记录，一切正常" as response text

#### Scenario: Warning detection response
- **WHEN** video detection result has risk_level="warning"
- **THEN** system uses template "检测到潜在风险，请注意安全" as response text

#### Scenario: Critical detection response
- **WHEN** video detection result has risk_level="critical"
- **THEN** system uses template "检测到摔倒，已通知紧急联系人" as response text

### Requirement: Video Detection TTS Audio Generation
The system SHALL generate TTS audio for video detection response text.

#### Scenario: Generate audio for safe detection
- **WHEN** video detection result is safe
- **THEN** system calls TTS service with "视频已记录，一切正常" and returns base64 audio

#### Scenario: Generate audio for critical detection
- **WHEN** video detection result is critical
- **THEN** system calls TTS service with "检测到摔倒，已通知紧急联系人" and returns base64 audio

### Requirement: Video Detection No Session Storage
The system SHALL NOT create or update session for video detection requests.

#### Scenario: Video detection without session
- **WHEN** client sends video input via /api_planning
- **THEN** system processes detection and returns result without creating session

#### Scenario: Video detection response format
- **WHEN** video detection completes
- **THEN** response contains {status: "recorded", result, response, audio} without session_id

### Requirement: Video Detection Alert Triggering
The system SHALL trigger emergency alert when critical risk is detected.

#### Scenario: Critical detection triggers alert
- **WHEN** video detection result has risk_level="critical"
- **THEN** system triggers emergency notification and sets alert_triggered=true in response

#### Scenario: Safe detection does not trigger alert
- **WHEN** video detection result has risk_level="safe"
- **THEN** system does not trigger any alert and alert_triggered=false or absent
