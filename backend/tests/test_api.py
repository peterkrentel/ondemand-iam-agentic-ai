"""
Tests for the AIMgentix API
"""
from fastapi.testclient import TestClient

from app.main import app
from app.db import init_db

# Initialize database before running tests
init_db()

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AIMgentix API"
    assert data["status"] == "operational"
    assert data["version"] == "0.1.0"
    assert "docs" in data


def test_openapi_docs():
    """Test that OpenAPI documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()


def test_create_event():
    """Test creating an audit event"""
    event_data = {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "agent_instance_id": "test-agent-001",
        "trace_id": "test-trace-123",
        "actor": "agent",
        "action_type": "tool_call",
        "resource": "test_tool",
        "status": "success",
        "latency_ms": 100,
        "metadata": {"test": "data"}
    }
    
    response = client.post("/v1/events", json=event_data)
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == event_data["event_id"]
    assert data["status"] == "captured"


def test_get_agent_events():
    """Test retrieving events for an agent"""
    # First create an event
    event_data = {
        "event_id": "550e8400-e29b-41d4-a716-446655440001",
        "agent_instance_id": "test-agent-002",
        "trace_id": "test-trace-124",
        "actor": "agent",
        "action_type": "tool_call",
        "resource": "test_tool",
        "status": "success"
    }
    
    response = client.post("/v1/events", json=event_data)
    assert response.status_code == 201
    
    # Now retrieve events
    response = client.get("/v1/agents/test-agent-002/events")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total" in data
    assert data["agent_instance_id"] == "test-agent-002"
    assert data["total"] >= 1


def test_get_agent_events_with_limit():
    """Test retrieving events with limit parameter"""
    response = client.get("/v1/agents/test-agent-002/events?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) <= 5


def test_create_event_validation():
    """Test that event validation works"""
    invalid_event = {
        "event_id": "invalid",
        # Missing required fields
    }
    
    response = client.post("/v1/events", json=invalid_event)
    assert response.status_code == 422  # Validation error


def test_actor_types():
    """Test different actor types"""
    for i, actor in enumerate(["agent", "human", "system"]):
        event_data = {
            "event_id": f"550e8400-e29b-41d4-a716-446655442{i:03d}",
            "agent_instance_id": f"test-agent-{actor}",
            "trace_id": f"test-trace-{actor}",
            "actor": actor,
            "action_type": "tool_call",
            "resource": "test_tool",
            "status": "success"
        }
        
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 201


def test_action_types():
    """Test different action types"""
    action_types = ["tool_call", "http_request", "db_query", "file_read", "file_write", "api_call"]
    
    for i, action_type in enumerate(action_types):
        event_data = {
            "event_id": f"550e8400-e29b-41d4-a716-446655441{i:03d}",
            "agent_instance_id": "test-agent-actions",
            "trace_id": "test-trace-actions",
            "actor": "agent",
            "action_type": action_type,
            "resource": f"test_{action_type}",
            "status": "success"
        }
        
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 201


def test_event_status_types():
    """Test different event status types"""
    for i, status in enumerate(["success", "error", "pending"]):
        event_data = {
            "event_id": f"550e8400-e29b-41d4-a716-446655443{i:03d}",
            "agent_instance_id": "test-agent-status",
            "trace_id": "test-trace-status",
            "actor": "agent",
            "action_type": "tool_call",
            "resource": "test_tool",
            "status": status
        }
        
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 201
