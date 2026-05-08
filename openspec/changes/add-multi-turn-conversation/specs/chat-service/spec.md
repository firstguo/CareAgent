## MODIFIED Requirements

### Requirement: /api_planning Endpoint Behavior
The /api_planning endpoint SHALL route requests to synchronous conversation flow or asynchronous task flow based on input type.

#### Scenario: Route text input to synchronous conversation
- **WHEN** client sends POST /api_planning with input.type="text"
- **THEN** system processes synchronously and returns conversation response with session_id

#### Scenario: Route voice input to synchronous conversation
- **WHEN** client sends POST /api_planning with input.type="voice"
- **THEN** system converts speech to text, processes synchronously, and returns conversation response with session_id

#### Scenario: Route image input to asynchronous task
- **WHEN** client sends POST /api_planning with input.type="image"
- **THEN** system creates async task and returns task_id for polling (existing behavior unchanged)

#### Scenario: Route video input to asynchronous task
- **WHEN** client sends POST /api_planning with input.type="video"
- **THEN** system creates async task and returns task_id for polling (existing behavior unchanged)

#### Scenario: Route multimodal input to asynchronous task
- **WHEN** client sends POST /api_planning with input.type="multimodal"
- **THEN** system creates async task and returns task_id for polling (existing behavior unchanged)

### Requirement: Response Format Differentiation
The /api_planning endpoint SHALL return different response formats based on processing mode (conversation vs task).

#### Scenario: Conversation mode response includes session_id
- **WHEN** processing text/voice input
- **THEN** response contains mode="conversation", session_id, response text, and is_new_session flag

#### Scenario: Task mode response includes task_id
- **WHEN** processing image/video input
- **THEN** response contains mode="task", task_id, and status="pending"

#### Scenario: Response includes mode field for client differentiation
- **WHEN** client receives response from /api_planning
- **THEN** client can check mode field to determine if response is synchronous (conversation) or requires polling (task)

### Requirement: Backward Compatibility
The /api_planning endpoint SHALL maintain backward compatibility for existing async task functionality while adding new conversation capabilities.

#### Scenario: Existing task status endpoint still works
- **WHEN** client queries GET /api_task_status/{task_id}
- **THEN** system returns task status as before (unchanged)

#### Scenario: Existing task input format still accepted
- **WHEN** client sends task input with notification, event_type fields
- **THEN** system processes async task correctly (unchanged)

#### Scenario: Client can detect new vs old behavior
- **WHEN** client receives response
- **THEN** client checks for presence of "mode" field to determine processing type (conversation vs task)
