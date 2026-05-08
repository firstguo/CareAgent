## ADDED Requirements

### Requirement: Session Message Storage
The system SHALL store conversation messages in session documents with proper structure and limits.

#### Scenario: Store user message
- **WHEN** user sends a message
- **THEN** message is stored with role="user", content=text, timestamp=ISODate

#### Scenario: Store assistant message
- **WHEN** LLM generates response
- **THEN** message is stored with role="assistant", content=response_text, timestamp=ISODate

#### Scenario: Enforce 50 message limit per session
- **WHEN** session.messages array reaches 50 messages
- **THEN** oldest messages are automatically removed using MongoDB $slice: -50 operator

### Requirement: Message Retrieval for Context
The system SHALL retrieve recent messages from session for LLM context building.

#### Scenario: Retrieve last 10 messages
- **WHEN** building LLM context for active session
- **THEN** system retrieves last 10 messages from session.messages array

#### Scenario: Handle empty session
- **WHEN** session is newly created with no messages
- **THEN** context building skips session history and only includes system prompt and mem0 memories

#### Scenario: Convert session messages to LangChain format
- **WHEN** retrieving messages for LLM
- **THEN** messages are converted to HumanMessage (role="user") and AIMessage (role="assistant") objects

### Requirement: MongoDB Sessions Collection Schema
The system SHALL use MongoDB sessions collection with defined schema and indexes.

#### Scenario: Session document structure
- **WHEN** creating a new session
- **THEN** document contains: _id, session_key, user_id, status, created_at, last_active, messages, expire_at

#### Scenario: Create unique index on session_key
- **WHEN** chat-service starts up
- **THEN** MongoDB creates unique index on session_key field to prevent duplicate active sessions

#### Scenario: Create TTL index on expire_at
- **WHEN** chat-service starts up
- **THEN** MongoDB creates TTL index on expire_at field with expireAfterSeconds=0 for automatic cleanup

#### Scenario: Session key format uniqueness
- **WHEN** creating session for user_id
- **THEN** session_key is formatted as "{user_id}:active" ensuring one active session per user

### Requirement: Session Status Transitions
The system SHALL manage session status transitions from active to expired.

#### Scenario: Mark session as expired on timeout
- **WHEN** new session is created and old active session exists
- **THEN** old session status is updated to "expired" with expired_at timestamp

#### Scenario: Prevent updates to expired sessions
- **WHEN** attempting to update session with status="expired"
- **THEN** operation fails and creates new session instead

#### Scenario: Expired session cleanup by TTL
- **WHEN** session expire_at timestamp is reached
- **THEN** MongoDB automatically deletes the session document (within 1 minute)
