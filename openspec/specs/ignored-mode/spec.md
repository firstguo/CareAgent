## ADDED Requirements

### Requirement: Ignored Mode Response
The system SHALL return ignored mode for non-dangerous video detections without calling LLM or creating session.

#### Scenario: Return ignored for normal video
- **WHEN** video detection result has risk_level="normal"
- **THEN** response contains {mode: "ignored", status: "ignored", reason: "no_risk_detected", result: {...}}

#### Scenario: Ignored response does not include session
- **WHEN** response mode is "ignored"
- **THEN** response does not contain session_id, audio_confirm, or schedule fields

#### Scenario: Ignored response does not create session
- **WHEN** video detection result is normal
- **THEN** system does not create or update any session

### Requirement: Conversation Mode for Dangerous Video
The system SHALL treat dangerous video detections as conversation input and process through normal conversation flow.

#### Scenario: Dangerous video creates new session
- **WHEN** video detection result has risk_level="critical" or "warning"
- **THEN** system creates new session for the dangerous event

#### Scenario: Dangerous video generates audio
- **WHEN** video detection triggers conversation
- **THEN** response includes audio_confirm with TTS of LLM response

#### Scenario: Dangerous video can trigger schedule
- **WHEN** LLM detects schedule intent from dangerous video context
- **THEN** response includes schedule object with audio_reminder
