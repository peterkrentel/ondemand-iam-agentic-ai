"""
Event types and models for AIMgentix SDK
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
import uuid


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
    POLICY_CHECK = "policy_check"  # AIMgentix policy evaluation


class EventStatus(str, Enum):
    """Status of the event"""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    DENIED = "denied"  # Policy denied the action


@dataclass
class AuditEvent:
    """
    Audit event data class
    """

    agent_instance_id: str
    trace_id: str
    actor: ActorType
    action_type: ActionType
    resource: str
    status: EventStatus
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["actor"] = self.actor.value
        data["action_type"] = self.action_type.value
        data["status"] = self.status.value
        return data
