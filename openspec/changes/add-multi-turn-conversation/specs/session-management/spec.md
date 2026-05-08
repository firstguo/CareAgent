## ADDED Requirements

### Requirement: Session Lifecycle Management
The system SHALL manage session lifecycle including creation, activation, timeout, and expiration for each user.

#### Scenario: Create new session for first message
- **WHEN** user sends first message with no active session
- **THEN** system creates a new session with status "active" and empty messages array

#### Scenario: Reuse active session within 10s window
- **WHEN** user sends message and has an active session with last_active within 10 seconds
- **THEN** system reuses the existing session and updates last_active timestamp

#### Scenario: Create new session after 10s timeout
- **WHEN** user sends message but last active session has last_active older than 10 seconds
- **THEN** system marks old session as "expired" and creates a new active session

#### Scenario: Auto-cleanup expired sessions via TTL
- **WHEN** session expire_at timestamp is reached
- **THEN** MongoDB TTL index automatically deletes the session document

### Requirement: Concurrent Session Access Safety
The system SHALL ensure thread-safe session operations across multiple instances using atomic MongoDB operations.

#### Scenario: Two concurrent requests for same user
- **WHEN** two requests arrive simultaneously for the same user_id
- **THEN** only one session is created or updated, the other request retries or uses the same session

#### Scenario: Atomic session update with find_one_and_update
- **WHEN** updating session last_active and appending messages
- **THEN** operation uses find_one_and_update to ensure atomicity

#### Scenario: Handle duplicate key error during session creation
- **WHEN** concurrent requests both attempt to create new session
- **THEN** system catches DuplicateKeyError and retries the operation (max 3 attempts with exponential backoff)

### Requirement: Session Key Uniqueness
The system SHALL enforce that each user has at most one active session at any time using unique index on session_key.

#### Scenario: Unique index prevents multiple active sessions
- **WHEN** attempting to create second active session for same user
- **THEN** MongoDB rejects the insert due to unique constraint on session_key

#### Scenario: Session key format
- **WHEN** creating session for user_id "user_001"
- **THEN** session_key is set to "user_001:active"

### Requirement: Session Message Storage
The system SHALL store conversation messages in session with maximum limit of 50 messages.

#### Scenario: Append messages to session
- **WHEN** user and assistant exchange messages in a session
- **THEN** messages are appended to session.messages array with role, content, and timestamp

#### Scenario: Enforce 50 message limit
- **WHEN** session.messages array reaches 50 messages
- **THEN** oldest messages are automatically removed using MongoDB $slice operator

#### Scenario: Message format
- **WHEN** storing a message
- **THEN** message object contains role ("user" or "assistant"), content (string), and timestamp (ISODate)

### Requirement: Session Timeout Configuration
The system SHALL support configurable timeout thresholds for different input types.

#### Scenario: Default 10s timeout for text input
- **WHEN** processing text input
- **THEN** session timeout is 10 seconds

#### Scenario: Extended 30s timeout for voice input
- **WHEN** processing voice input (requires ASR processing time)
- **THEN** session timeout is 30 seconds

#### Scenario: Timeout threshold from environment variable
- **WHEN** system starts
- **THEN** timeout values are read from SESSION_TIMEOUT_TEXT and SESSION_TIMEOUT_VOICE environment variables with defaults 10s and 30s
