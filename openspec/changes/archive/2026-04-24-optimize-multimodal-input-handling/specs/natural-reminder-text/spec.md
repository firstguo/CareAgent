## ADDED Requirements

### Requirement: Natural Reminder Text Mapping
The system SHALL use predefined natural expression mapping to generate reminder audio text based on schedule type, instead of using raw message field.

#### Scenario: Medication reminder uses natural expression
- **WHEN** schedule type is "medication_reminder"
- **THEN** system uses "该吃药了！" as reminder text for TTS

#### Scenario: Meal reminder uses natural expression
- **WHEN** schedule type is "meal_reminder"
- **THEN** system uses "吃饭时间到了，记得按时用餐" as reminder text for TTS

#### Scenario: Care check reminder uses natural expression
- **WHEN** schedule type is "care_check"
- **THEN** system uses "该做健康检查了" as reminder text for TTS

#### Scenario: Custom reminder uses message field
- **WHEN** schedule type is "custom" or not in mapping
- **THEN** system uses the message field as reminder text for TTS

### Requirement: Reminder Text Mapping Function
The system SHALL provide a function to retrieve natural reminder text based on schedule type and message.

#### Scenario: Get natural text for known type
- **WHEN** get_natural_reminder_text("medication_reminder", "提醒吃药") is called
- **THEN** returns "该吃药了！"

#### Scenario: Get natural text for unknown type
- **WHEN** get_natural_reminder_text("unknown_type", "自定义提醒") is called
- **THEN** returns "自定义提醒" (uses message field)

#### Scenario: Get natural text for custom type
- **WHEN** get_natural_reminder_text("custom", "每天喝水") is called
- **THEN** returns "每天喝水" (uses message field)

### Requirement: Mapping Table Extensibility
The system SHALL store reminder text mapping in a configurable data structure for easy extension.

#### Scenario: Mapping table is defined as constant
- **WHEN** system loads
- **THEN** REMINDER_TEXT_MAP constant contains predefined mappings for medication_reminder, meal_reminder, care_check

#### Scenario: New type can be added to mapping
- **WHEN** developer adds new entry to REMINDER_TEXT_MAP
- **THEN** system automatically uses new mapping without code changes
