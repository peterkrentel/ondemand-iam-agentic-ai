# 📋 API Specification

**AIMgentix - Agent Audit Trail API**

Version: 0.1.0

---

## Base URL

```
http://localhost:8000
```

For production deployments, use your deployed URL.

---

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Authentication

Currently no authentication is required (development mode).

**Production deployments should implement:**
- API key authentication
- JWT tokens
- OAuth 2.0

---

## Endpoints

### Health Check

**GET** `/`

Check API health and get version information.

**Response** (200 OK):
```json
{
  "service": "AIMgentix API",
  "status": "operational",
  "version": "0.1.0",
  "docs": "/docs"
}
```

---

### Capture Audit Event

**POST** `/v1/events`

Capture a new audit event from an agent.

**Request Body**:
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-25T10:30:00Z",
  "agent_instance_id": "agent-langchain-001",
  "trace_id": "trace-abc123",
  "actor": "agent",
  "action_type": "tool_call",
  "resource": "web_search",
  "status": "success",
  "latency_ms": 342,
  "metadata": {
    "tool_name": "DuckDuckGo",
    "query": "[REDACTED]"
  }
}
```

**Fields**:
- `event_id` (string, required): Unique event identifier (UUID)
- `timestamp` (string, ISO8601): Event timestamp (auto-generated if not provided)
- `agent_instance_id` (string, required): Unique agent instance identifier
- `trace_id` (string, required): Trace ID for correlating related events
- `actor` (string, required): Type of actor - one of: `agent`, `human`, `system`
- `action_type` (string, required): Type of action - one of: `tool_call`, `http_request`, `db_query`, `file_read`, `file_write`, `api_call`
- `resource` (string, required): Resource being accessed (URL, file path, tool name, etc.)
- `status` (string, required): Status - one of: `success`, `error`, `pending`
- `latency_ms` (integer, optional): Latency in milliseconds
- `metadata` (object, optional): Additional context (redacted by default)

**Response** (201 Created):
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "captured"
}
```

**Error Response** (500 Internal Server Error):
```json
{
  "detail": "Failed to capture event: <error message>"
}
```

---

### Get Agent Events

**GET** `/v1/agents/{agent_id}/events`

Retrieve audit events for a specific agent.

**Path Parameters**:
- `agent_id` (string, required): Unique agent instance identifier

**Query Parameters**:
- `limit` (integer, optional): Maximum number of events to return (default: 100)

**Response** (200 OK):
```json
{
  "events": [
    {
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2026-01-25T10:30:00Z",
      "agent_instance_id": "agent-langchain-001",
      "trace_id": "trace-abc123",
      "actor": "agent",
      "action_type": "tool_call",
      "resource": "web_search",
      "status": "success",
      "latency_ms": 342,
      "metadata": {
        "tool_name": "DuckDuckGo",
        "query": "[REDACTED]"
      }
    }
  ],
  "total": 150,
  "agent_instance_id": "agent-langchain-001"
}
```

**Error Response** (500 Internal Server Error):
```json
{
  "detail": "Failed to retrieve events: <error message>"
}
```

---

## Data Models

### ActorType (Enum)
- `agent`: AI agent
- `human`: Human operator
- `system`: System process

### ActionType (Enum)
- `tool_call`: Agent tool invocation
- `http_request`: HTTP API request
- `db_query`: Database query
- `file_read`: File read operation
- `file_write`: File write operation
- `api_call`: External API call

### EventStatus (Enum)
- `success`: Operation completed successfully
- `error`: Operation failed
- `pending`: Operation in progress

---

## Privacy & Security

### Privacy-First Design

- **Redaction by default**: Sensitive data in metadata is redacted by default
- **Opt-in capture**: Only capture what you explicitly specify
- **Minimal data**: Event schema captures only essential audit information

### Best Practices

1. **Don't capture PII**: Avoid logging personally identifiable information
2. **Redact sensitive data**: Use `[REDACTED]` for sensitive fields
3. **Use UUIDs**: Generate random UUIDs for event_id
4. **Set trace_id**: Use consistent trace_id for related events
5. **Implement auth**: Add authentication in production

---

## Rate Limits

Currently no rate limits (development mode).

**Production recommendations:**
- 1000 requests/minute per agent
- 10,000 events/day per agent
- Implement backoff/retry logic in SDK

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Event captured successfully
- `400 Bad Request`: Invalid request body
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## SDK Integration

### Python SDK

```python
from ondemand_iam_agentic_ai import AuditClient, AuditEvent, ActorType, ActionType, EventStatus

# Initialize client
audit_client = AuditClient(api_url="http://localhost:8000")

# Capture an event
event = AuditEvent(
    agent_instance_id="my-agent-001",
    trace_id="trace-abc123",
    actor=ActorType.AGENT,
    action_type=ActionType.TOOL_CALL,
    resource="web_search",
    status=EventStatus.SUCCESS,
    latency_ms=342
)

audit_client.capture(event)
```

---

## Testing

### Health Check
```bash
curl http://localhost:8000/
```

### Capture Event
```bash
curl -X POST http://localhost:8000/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent_instance_id": "test-agent",
    "trace_id": "test-trace",
    "actor": "agent",
    "action_type": "tool_call",
    "resource": "test_tool",
    "status": "success"
  }'
```

### Get Events
```bash
curl http://localhost:8000/v1/agents/test-agent/events
```

---

## Version History

### v0.1.0 (2026-01-31)
- Initial API specification
- Core event capture and retrieval endpoints
- OpenAPI/Swagger documentation
- Privacy-first design

---

## Support

- **Documentation**: [GitHub Repository](https://github.com/peterkrentel/ondemand-iam-agentic-ai)
- **Issues**: [GitHub Issues](https://github.com/peterkrentel/ondemand-iam-agentic-ai/issues)

---

**Built with FastAPI • MIT License • 2026**
