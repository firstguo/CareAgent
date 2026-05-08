## ADDED Requirements

### Requirement: Unified Synchronous Processing
The system SHALL process all input types (text, voice, video) synchronously and return results directly without polling.

#### Scenario: Text input returns synchronously
- **WHEN** user sends text input
- **THEN** system processes conversation and returns result immediately

#### Scenario: Voice input returns synchronously
- **WHEN** user sends voice input
- **THEN** system transcribes audio, processes conversation, and returns result immediately

#### Scenario: Video input returns synchronously
- **WHEN** user sends video input
- **THEN** system performs fall detection and returns result immediately (no task_id, no polling)

### Requirement: Input Type Routing
The system SHALL route different input types to appropriate processing logic at the entry point.

#### Scenario: Route text input to conversation
- **WHEN** input.type is "text"
- **THEN** system directly calls conversation flow

#### Scenario: Route voice input to ASR then conversation
- **WHEN** input.type is "voice"
- **THEN** system transcribes audio to text, then calls conversation flow

#### Scenario: Route video input to pre-detection
- **WHEN** input.type is "video"
- **THEN** system performs fall detection before deciding processing path
