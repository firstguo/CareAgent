## ADDED Requirements

### Requirement: Dual Audio Response for Schedule Detection
The system SHALL return two separate audio files when schedule intent is detected in conversation: audio_confirm for immediate playback and audio_reminder for scheduled playback.

#### Scenario: Return dual audio when schedule detected
- **WHEN** user message contains schedule intent (e.g., "每天早上8点提醒吃药")
- **THEN** response includes both audio_confirm and audio_reminder fields

#### Scenario: audio_confirm contains conversation response
- **WHEN** schedule is detected
- **THEN** audio_confirm contains TTS of conversation response (e.g., "好的，已设置每天早上8点提醒你吃药")

#### Scenario: audio_reminder contains natural reminder text
- **WHEN** schedule is detected
- **THEN** audio_reminder contains TTS of natural reminder text (e.g., "该吃药了！")

### Requirement: Schedule Object Contains Audio Reminder
The system SHALL include audio_reminder in the schedule object for frontend storage and scheduled playback.

#### Scenario: Schedule includes audio_reminder
- **WHEN** schedule intent is detected
- **THEN** schedule object contains {cron, message, type, audio_reminder}

#### Scenario: Frontend can store audio_reminder
- **WHEN** frontend receives schedule with audio_reminder
- **THEN** frontend can save audio_reminder to localStorage for scheduled playback

### Requirement: Non-Schedule Conversation Returns Single Audio
The system SHALL return only audio_confirm (not audio_reminder) when no schedule intent is detected.

#### Scenario: No schedule detected returns single audio
- **WHEN** user message does not contain schedule intent
- **THEN** response includes audio_confirm but not audio_reminder

#### Scenario: audio_reminder is null or absent for non-schedule
- **WHEN** no schedule detected
- **THEN** audio_reminder field is null or absent in response

### Requirement: Audio Generation for Voice Input
The system SHALL generate dual audio for voice input with schedule intent, same as text input.

#### Scenario: Voice input with schedule intent
- **WHEN** user sends voice input and ASR result contains schedule intent
- **THEN** system returns dual audio (audio_confirm + audio_reminder) same as text input

#### Scenario: Voice input without schedule intent
- **WHEN** user sends voice input without schedule intent
- **THEN** system returns only audio_confirm
