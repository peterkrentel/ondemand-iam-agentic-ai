"""
Event models for the OnDemand IAM Agentic AI API
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ActorType(str, Enum):
    """Type of actor performing the action"""
    AGENT = "agent"
    HUMAN = "human"
    SYSTEM = "system"


class ActionType(str, Enum):
    """Type of action being performed"""
    TOOL_CALL = "tool_call"
    HTTP_REQUEST = "http_request"
    DB_QUERY = "db_query"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    API_CALL = "api_call"


class EventStatus(str, Enum):
    """Status of the event"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class AuditEvent(BaseModel):
    """
    Core audit event schema
    Privacy-first: redaction by default, opt-in for full payload capture
    """
    event_id: str = Field(..., description="Unique event identifier (UUID)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="ISO8601 timestamp")
    agent_instance_id: str = Field(..., description="Unique agent instance identifier")
    trace_id: str = Field(..., description="Trace ID for correlating related events")
    actor: ActorType = Field(..., description="Type of actor (agent, human, system)")
    action_type: ActionType = Field(..., description="Type of action performed")
    resource: str = Field(..., description="Resource being accessed (URL, file path, etc.)")
    status: EventStatus = Field(..., description="Status of the action")
    latency_ms: Optional[int] = Field(None, description="Latency in milliseconds")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context (redacted by default)")

    class Config:
        json_schema_extra = {
            "example": {
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
        }


class AuditEventResponse(BaseModel):
    """Response model for audit event queries"""
    events: list[AuditEvent]
    total: int
    agent_instance_id: str

