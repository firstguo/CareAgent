## 1. Database Schema & Indexes

- [x] 1.1 Add sessions collection initialization in main.py startup event
- [x] 1.2 Create unique index on session_key field
- [x] 1.3 Create TTL index on expire_at field with expireAfterSeconds=0
- [x] 1.4 Create compound index on (user_id, last_active) for efficient session lookup

## 2. Session Management Module

- [x] 2.1 Create services/chat-service/modules/session.py file
- [x] 2.2 Implement SessionManager class with MongoDB connection
- [x] 2.3 Implement get_or_create_session() method with atomic find_one_and_update
- [x] 2.4 Implement update_session() method to append messages and update last_active
- [x] 2.5 Implement expire_old_session() method to mark previous sessions as expired
- [x] 2.6 Add retry logic with exponential backoff for DuplicateKeyError handling
- [x] 2.7 Add configurable timeout thresholds (SESSION_TIMEOUT_TEXT, SESSION_TIMEOUT_VOICE)

## 3. Session Data Models

- [x] 3.1 Define SessionData Pydantic model with all required fields
- [x] 3.2 Define MessageData Pydantic model (role, content, timestamp)
- [x] 3.3 Add session_id and is_new_session fields to response models
- [x] 3.4 Add mode field to response model (conversation vs task)

## 4. Conversation Execution Logic

- [x] 4.1 Create execute_conversation() function in executor.py
- [x] 4.2 Implement dual-layer context building (session messages + mem0 search)
- [x] 4.3 Implement session message retrieval (last 10 messages)
- [x] 4.4 Implement mem0 memory search with current message as query
- [x] 4.5 Implement LangChain message format conversion (session → HumanMessage/AIMessage)
- [x] 4.6 Implement LLM prompt construction with system + memories + history + current
- [x] 4.7 Add session message storage after LLM response (append user + assistant messages)
- [x] 4.8 Add mem0 fact extraction and storage after conversation

## 5. API Endpoint Modification

- [x] 5.1 Modify /api_planning endpoint to check input.type
- [x] 5.2 Add routing logic: text/voice → execute_conversation(), image/video → execute_task()
- [x] 5.3 Implement synchronous conversation response format (mode, session_id, response, is_new_session)
- [x] 5.4 Add mode field to async task response (mode="task", task_id)
- [x] 5.5 Update response model to support both conversation and task modes
- [x] 5.6 Add error handling for session creation failures

## 6. Memory Module Enhancements

- [x] 6.1 Optimize mem0 search to use top_k=3 (reduce latency)
- [x] 6.2 Add memory formatting function for LLM context (User Information: ...)
- [x] 6.3 Add conditional mem0.add() call (only extract facts, not every message)

## 7. Configuration & Environment

- [x] 7.1 Add SESSION_TIMEOUT_TEXT environment variable (default: 10 seconds)
- [x] 7.2 Add SESSION_TIMEOUT_VOICE environment variable (default: 30 seconds)
- [x] 7.3 Add SESSION_MESSAGE_LIMIT environment variable (default: 50 messages)
- [x] 7.4 Add CONTEXT_HISTORY_LIMIT environment variable (default: 10 messages)
- [x] 7.5 Update .env.example with new configuration options

## 8. Logging & Monitoring

- [x] 8.1 Add structured logging for session creation events
- [x] 8.2 Add structured logging for session reuse events
- [x] 8.3 Add structured logging for session timeout events
- [x] 8.4 Add structured logging for concurrent conflict retries
- [x] 8.5 Add response time tracking for conversation vs task modes

## 9. Testing

- [ ] 9.1 Write unit tests for SessionManager.get_or_create_session()
- [ ] 9.2 Write unit tests for concurrent session creation (mock DuplicateKeyError)
- [ ] 9.3 Write unit tests for session timeout logic
- [ ] 9.4 Write unit tests for context building (session + mem0)
- [ ] 9.5 Write integration test for /api_planning with text input
- [ ] 9.6 Write integration test for multi-turn conversation (2+ messages within 10s)
- [ ] 9.7 Write integration test for session timeout and new session creation
- [ ] 9.8 Write integration test for backward compatibility (image/video still async)

## 10. Documentation & Migration

- [ ] 10.1 Update API documentation with new response formats
- [ ] 10.2 Add migration guide for frontend developers (detect mode field)
- [ ] 10.3 Add example code for handling conversation vs task responses
- [ ] 10.4 Update frontend app.py to support new response format (optional)
