# Event Schema Contract (v1)

**Status**: Active
**Last Updated**: 2026-02-01
**Applies To**: SDK → API → Database → UI
**Why This Exists**: Event schema crosses all system boundaries. Changes break clients.
**Validation**: `backend/app/models.py` (Pydantic), `backend/tests/test_contracts.py`

---

## Public vs Internal Boundary

**This schema is considered public API once exposed to customers.**

Once customers send events via the SDK, this schema MUST NOT break compatibility without a major version bump.

---

## Required Envelope

All events MUST include these fields:

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `event_id` | string | YES | MUST be UUID v4 format |
| `timestamp` | string | YES | MUST be ISO 8601 with timezone (e.g., `2026-01-25T10:30:00Z`) |
| `agent_instance_id` | string | YES | MUST be non-empty, max 255 chars |
| `trace_id` | string | YES | MUST be non-empty, max 255 chars |
| `actor` | string | YES | MUST be one of: `agent`, `human`, `system` |
| `action_type` | string | YES | MUST be one of: `tool_call`, `http_request`, `db_query`, `file_read`, `file_write`, `api_call` |
| `resource` | string | YES | MUST be non-empty, max 1024 chars |
| `status` | string | YES | MUST be one of: `success`, `error`, `pending` |
| `latency_ms` | integer \| null | NO | If present, MUST be >= 0 |
| `metadata` | object \| null | NO | If present, MUST be valid JSON object |

---

## Field Semantics

### `event_id`
- **Purpose**: Unique identifier for this specific event
- **Uniqueness**: MUST be globally unique across all events
- **Idempotency**: Events with duplicate `event_id` MUST be treated as the same event (no duplicate storage)
- **Format**: UUID v4 (e.g., `550e8400-e29b-41d4-a716-446655440000`)

### `timestamp`
- **Purpose**: When the event occurred (NOT when it was received)
- **Format**: ISO 8601 with timezone (e.g., `2026-01-25T10:30:00Z` or `2026-01-25T10:30:00.123Z`)
- **Timezone**: MUST include timezone (Z for UTC or +HH:MM offset)
- **Validation**: Future timestamps are allowed (no validation)

### `agent_instance_id`
- **Purpose**: Identifies which agent instance performed the action
- **Uniqueness**: Multiple events MAY share the same `agent_instance_id`
- **Format**: Opaque string (no specific format required)
- **Example**: `demo-agent-001`, `langchain-prod-7f3a`

### `trace_id`
- **Purpose**: Groups related events (e.g., a single agent run or task)
- **Correlation**: All events with the same `trace_id` SHOULD have the same `agent_instance_id`
- **Format**: Opaque string (no specific format required)
- **Example**: `trace-abc123`, `run-20260125-103000`

### `actor`
- **Purpose**: Who/what initiated the action
- **Values**:
  - `agent` - Action performed by AI agent
  - `human` - Action performed by human user
  - `system` - Action performed by system/automation
- **Extensibility**: New values MAY be added in future versions

### `action_type`
- **Purpose**: What kind of action was performed
- **Values**:
  - `tool_call` - Agent called a tool/function
  - `http_request` - HTTP API call
  - `db_query` - Database query
  - `file_read` - File read operation
  - `file_write` - File write operation
  - `api_call` - Generic API call
- **Extensibility**: New values MAY be added in future versions

### `resource`
- **Purpose**: What resource was accessed
- **Format**: Free-form string describing the resource
- **Examples**: `web_search`, `https://api.example.com/search`, `/path/to/file.txt`
- **Privacy**: SHOULD NOT contain sensitive data (use metadata for that)

### `status`
- **Purpose**: Outcome of the action
- **Values**:
  - `success` - Action completed successfully
  - `error` - Action failed
  - `pending` - Action is in progress (rare)
- **Extensibility**: New values MAY be added in future versions

### `latency_ms`
- **Purpose**: How long the action took (milliseconds)
- **Optional**: MAY be null if latency is unknown
- **Constraints**: If present, MUST be >= 0

### `metadata`
- **Purpose**: Additional context specific to the action
- **Optional**: MAY be null or empty object
- **Privacy**: SHOULD redact sensitive data by default
- **Format**: Any valid JSON object (no schema enforced)

---

## Unknown Fields Policy

**Rule**: Unknown fields MUST be ignored (forward compatibility).

**Rationale**: Allows new SDK versions to send additional fields without breaking old API versions.

**Storage**: Unknown fields MAY be stored or MAY be stripped (implementation choice).

---

## Backwards Compatibility Rules

**Simple rule**: Backward-compatible changes add optional fields; breaking changes rename, remove, or change semantics of existing fields.

### ✅ ALLOWED (non-breaking changes):
- Adding new optional fields
- Adding new enum values to `actor`, `action_type`, `status`
- Relaxing validation constraints
- Adding fields to `metadata`

### ❌ NOT ALLOWED (breaking changes):
- Removing required fields
- Changing field types
- Removing enum values
- Renaming fields
- Making optional fields required
- Changing field semantics

**Breaking changes require a major version bump (v2).**

---

## Validation Behavior

### API MUST return 400 Bad Request when:
- Required field is missing
- Field type is wrong (e.g., string instead of integer)
- Enum value is invalid
- `event_id` is not a valid UUID
- `timestamp` is not valid ISO 8601
- `latency_ms` is negative

### API MUST return 201 Created when:
- All required fields are present and valid
- Even if storage fails (fail-open behavior)
- Even if event_id is duplicate (idempotent)

---

## Acceptance Criteria (Examples)

### EC-1: ✅ Valid Event (Minimal)
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-25T10:30:00Z",
  "agent_instance_id": "demo-agent-001",
  "trace_id": "trace-abc123",
  "actor": "agent",
  "action_type": "tool_call",
  "resource": "web_search",
  "status": "success"
}
```

### EC-2: ✅ Valid Event (Full)
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-25T10:30:00.123Z",
  "agent_instance_id": "demo-agent-001",
  "trace_id": "trace-abc123",
  "actor": "agent",
  "action_type": "http_request",
  "resource": "https://api.example.com/search",
  "status": "success",
  "latency_ms": 342,
  "metadata": {
    "method": "GET",
    "status_code": 200
  }
}
```

### EC-3: ✅ Valid Event (With Unknown Field - Forward Compat)
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-25T10:30:00Z",
  "agent_instance_id": "demo-agent-001",
  "trace_id": "trace-abc123",
  "actor": "agent",
  "action_type": "tool_call",
  "resource": "web_search",
  "status": "success",
  "future_field": "ignored by v1 API"
}
```
**Expected**: API accepts and ignores `future_field`

### EC-4: ❌ Invalid Event (Missing Required Field)
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-25T10:30:00Z",
  "agent_instance_id": "demo-agent-001"
}
```
**Expected**: 400 Bad Request - Missing `trace_id`, `actor`, `action_type`, `resource`, `status`

### EC-5: ❌ Invalid Event (Wrong Enum Value)
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-25T10:30:00Z",
  "agent_instance_id": "demo-agent-001",
  "trace_id": "trace-abc123",
  "actor": "robot",
  "action_type": "tool_call",
  "resource": "web_search",
  "status": "success"
}
```
**Expected**: 400 Bad Request - `actor` must be `agent`, `human`, or `system`

### EC-6: ❌ Invalid Event (Negative Latency)
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-25T10:30:00Z",
  "agent_instance_id": "demo-agent-001",
  "trace_id": "trace-abc123",
  "actor": "agent",
  "action_type": "tool_call",
  "resource": "web_search",
  "status": "success",
  "latency_ms": -100
}
```
**Expected**: 400 Bad Request - `latency_ms` must be >= 0

---

## Validation

**Current State**: ✅ Fully validated

**Enforcement**:
1. ✅ Pydantic models in `backend/app/models.py` enforce schema at runtime
2. ✅ Contract tests in `backend/tests/test_contracts.py` validate:
   - Required fields are enforced
   - Enum values are validated
   - Type constraints are checked
   - OpenAPI schema matches code
   - SDK/API compatibility

**CI/CD**: Tests run on every commit via GitHub Actions

---

## When to Update This Spec

Update this spec when:
1. Adding a new field (document it here FIRST, then update code)
2. Adding a new enum value (document it here FIRST, then update code)
3. Changing field semantics (update spec, then code, then tests)
4. A bug reveals ambiguity (clarify the spec)

**Process**: Spec → Code → Tests (in that order)

---

## References

- **Implementation**: `backend/app/models.py` (Pydantic models)
- **SDK**: `sdk/aimgentix/events.py` (dataclasses)
- **Contract Tests**: `backend/tests/test_contracts.py`, `sdk/tests/test_contracts.py`
- **API Documentation**: `docs/API_SPEC.md` (descriptive)
- **Testing Guide**: `docs/CONTRACT_TESTING.md`

