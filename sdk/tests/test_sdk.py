"""
Tests for the AIMgentix SDK
"""
from unittest.mock import Mock, patch
import requests

from aimgentix import AuditClient, AuditEvent, ActorType, ActionType, EventStatus


def test_import():
    """Test that SDK can be imported"""
    assert AuditClient is not None
    assert AuditEvent is not None


def test_actor_type_enum():
    """Test ActorType enum values"""
    assert ActorType.AGENT.value == "agent"
    assert ActorType.HUMAN.value == "human"
    assert ActorType.SYSTEM.value == "system"


def test_action_type_enum():
    """Test ActionType enum values"""
    assert ActionType.TOOL_CALL.value == "tool_call"
    assert ActionType.HTTP_REQUEST.value == "http_request"
    assert ActionType.DB_QUERY.value == "db_query"
    assert ActionType.FILE_READ.value == "file_read"
    assert ActionType.FILE_WRITE.value == "file_write"
    assert ActionType.API_CALL.value == "api_call"
    assert ActionType.POLICY_CHECK.value == "policy_check"


def test_event_status_enum():
    """Test EventStatus enum values"""
    assert EventStatus.SUCCESS.value == "success"
    assert EventStatus.ERROR.value == "error"
    assert EventStatus.PENDING.value == "pending"
    assert EventStatus.DENIED.value == "denied"


def test_audit_event_creation():
    """Test creating an AuditEvent"""
    event = AuditEvent(
        agent_instance_id="test-agent",
        trace_id="test-trace",
        actor=ActorType.AGENT,
        action_type=ActionType.TOOL_CALL,
        resource="test_tool",
        status=EventStatus.SUCCESS,
        latency_ms=100
    )
    
    assert event.agent_instance_id == "test-agent"
    assert event.trace_id == "test-trace"
    assert event.actor == ActorType.AGENT
    assert event.action_type == ActionType.TOOL_CALL
    assert event.resource == "test_tool"
    assert event.status == EventStatus.SUCCESS
    assert event.latency_ms == 100
    assert event.event_id is not None
    assert event.timestamp is not None


def test_audit_event_with_metadata():
    """Test creating an AuditEvent with metadata"""
    event = AuditEvent(
        agent_instance_id="test-agent",
        trace_id="test-trace",
        actor=ActorType.AGENT,
        action_type=ActionType.TOOL_CALL,
        resource="test_tool",
        status=EventStatus.SUCCESS,
        metadata={"key": "value", "count": 42}
    )
    
    assert event.metadata == {"key": "value", "count": 42}


def test_audit_client_initialization():
    """Test AuditClient initialization"""
    client = AuditClient(api_url="http://localhost:8000")
    assert client.api_url == "http://localhost:8000"


@patch('requests.post')
def test_audit_client_capture(mock_post):
    """Test capturing an event with AuditClient"""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"event_id": "test-id", "status": "captured"}
    mock_post.return_value = mock_response
    
    client = AuditClient(api_url="http://localhost:8000")
    event = AuditEvent(
        agent_instance_id="test-agent",
        trace_id="test-trace",
        actor=ActorType.AGENT,
        action_type=ActionType.TOOL_CALL,
        resource="test_tool",
        status=EventStatus.SUCCESS
    )
    
    # Capture returns None (async buffering)
    client.capture(event)
    # Flush to send events
    client.flush()
    assert mock_post.called


@patch('requests.post')
def test_audit_client_capture_failure(mock_post):
    """Test handling capture failure"""
    mock_post.side_effect = requests.exceptions.RequestException("Connection error")
    
    client = AuditClient(api_url="http://localhost:8000")
    event = AuditEvent(
        agent_instance_id="test-agent",
        trace_id="test-trace",
        actor=ActorType.AGENT,
        action_type=ActionType.TOOL_CALL,
        resource="test_tool",
        status=EventStatus.SUCCESS
    )
    
    # Should not raise, just log error
    client.capture(event)
    # Flush will attempt to send and fail
    client.flush()
    # Client should gracefully handle the error
    assert mock_post.called


def test_audit_client_context_manager():
    """Test AuditClient as context manager"""
    with AuditClient(api_url="http://localhost:8000") as client:
        assert client is not None
        assert client.api_url == "http://localhost:8000"


@patch('requests.post')
def test_audit_client_buffer_and_flush(mock_post):
    """Test buffering and flushing events"""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"event_id": "test-id", "status": "captured"}
    mock_post.return_value = mock_response
    
    client = AuditClient(api_url="http://localhost:8000")
    
    # Create multiple events
    for i in range(3):
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id=f"test-trace-{i}",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_tool",
            status=EventStatus.SUCCESS
        )
        client.capture(event)
    
    # Flush should be called
    client.flush()
    assert mock_post.call_count >= 3
