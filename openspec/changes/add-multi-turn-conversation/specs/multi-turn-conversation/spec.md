## ADDED Requirements

### Requirement: Multi-Turn Conversation Flow
The system SHALL support multi-turn conversations within a session, maintaining context across multiple message exchanges.

#### Scenario: Process text input as synchronous conversation
- **WHEN** user sends text input via /api_planning
- **THEN** system processes synchronously and returns response within 15 seconds

#### Scenario: Process voice input as synchronous conversation
- **WHEN** user sends voice input via /api_planning
- **THEN** system converts speech to text, processes conversation, and returns response within 30 seconds

#### Scenario: Route image/video input to async task flow
- **WHEN** user sends image or video input via /api_planning
- **THEN** system creates async task and returns task_id for polling (existing behavior)

### Requirement: Dual-Layer Memory Context Building
The system SHALL build LLM context using both short-term session messages and long-term mem0 memories.

#### Scenario: Build context with session history
- **WHEN** generating LLM response
- **THEN** system includes last 10 messages from session.messages in conversation history

#### Scenario: Build context with mem0 long-term memory
- **WHEN** generating LLM response
- **THEN** system searches mem0 for relevant memories using current user message as query (top_k=3)

#### Scenario: Format mem0 memories for LLM
- **WHEN** mem0 returns search results
- **THEN** memories are formatted as "User Information: [memory content]" in the prompt

#### Scenario: Combine session and mem0 context
- **WHEN** building LLM messages array
- **THEN** order is: System prompt → mem0 memories → session messages (last 10) → current user message

### Requirement: Session Context Passing
The system SHALL pass complete session context to LLM for coherent multi-turn responses.

#### Scenario: Include system prompt
- **WHEN** building LLM messages
- **THEN** first message is SystemMessage with role "assistant" and caring caregiver persona

#### Scenario: Include conversation history from session
- **WHEN** user has exchanged multiple messages in current session
- **THEN** all messages from session.messages (up to 10) are included as HumanMessage and AIMessage

#### Scenario: Maintain context continuity
- **WHEN** user asks follow-up question referring to previous message
- **THEN** LLM can understand context from session history and provide coherent response

### Requirement: Synchronous Response Format
The system SHALL return conversation response synchronously with session information.

#### Scenario: Return response for new session
- **WHEN** user sends first message creating new session
- **THEN** response includes session_id, response text, audio (optional), is_new_session=true, message_count

#### Scenario: Return response for existing session
- **WHEN** user sends message reusing active session
- **THEN** response includes session_id, response text, audio (optional), is_new_session=false, message_count

#### Scenario: Response structure for conversation mode
- **WHEN** processing text/voice input
- **THEN** response format is:
```json
{
  "mode": "conversation",
  "session_id": "sess_xxx",
  "response": "AI response text",
  "audio_response": "base64_audio (optional)",
  "is_new_session": true,
  "message_count": 2
}
```

#### Scenario: Response structure for task mode (unchanged)
- **WHEN** processing image/video input
- **THEN** response format is:
```json
{
  "mode": "task",
  "task_id": "task_xxx",
  "status": "pending",
  "message": "任务已提交，正在处理中"
}
```

### Requirement: Memory Storage After Conversation
The system SHALL store conversation outcomes to both session and mem0 after generating response.

#### Scenario: Append messages to session
- **WHEN** LLM generates response
- **THEN** both user message and assistant message are appended to session.messages array

#### Scenario: Extract facts to mem0
- **WHEN** conversation completes
- **THEN** system calls mem0.add() to store extracted facts about user (e.g., health conditions, preferences)

#### Scenario: Update session last_active
- **WHEN** conversation completes
- **THEN** session.last_active is updated to current time and expire_at is extended
