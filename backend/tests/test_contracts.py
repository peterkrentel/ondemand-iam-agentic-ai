"""
Contract tests for AIMgentix API

These tests ensure that:
1. API contracts (Pydantic models) are consistent with SDK
2. OpenAPI schema is valid and accurate
3. All enum values are properly defined and handled
4. Schema changes don't break compatibility
"""
import pytest
from fastapi.testclient import TestClient
import json

from app.main import app
from app.models import ActorType, ActionType, EventStatus, AuditEvent
from app.db import init_db

# Initialize database before running tests
init_db()

client = TestClient(app)


class TestOpenAPIContract:
    """Test OpenAPI schema generation and validation"""
    
    def test_openapi_schema_exists(self):
        """Verify OpenAPI schema is generated"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert schema["openapi"].startswith("3.")
    
    def test_openapi_has_required_endpoints(self):
        """Verify all required endpoints are documented"""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]
        
        # Check required endpoints exist
        assert "/" in paths
        assert "/v1/events" in paths
        assert "/v1/agents/{agent_id}/events" in paths
    
    def test_openapi_event_schema_completeness(self):
        """Verify AuditEvent schema in OpenAPI is complete"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Find AuditEvent schema
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        assert "AuditEvent" in schemas
        
        event_schema = schemas["AuditEvent"]
        required_fields = event_schema.get("required", [])
        
        # Verify all required fields are present
        expected_required = [
            "event_id", "agent_instance_id", "trace_id",
            "actor", "action_type", "resource", "status"
        ]
        for field in expected_required:
            assert field in required_fields, f"Required field {field} missing from schema"
    
    def test_openapi_enum_definitions(self):
        """Verify enum types are properly defined in OpenAPI"""
        response = client.get("/openapi.json")
        schema = response.json()
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Check ActorType enum
        assert "ActorType" in schemas
        actor_enum = schemas["ActorType"]
        assert actor_enum["enum"] == ["agent", "human", "system"]
        
        # Check ActionType enum
        assert "ActionType" in schemas
        action_enum = schemas["ActionType"]
        assert sorted(action_enum["enum"]) == sorted([
            "tool_call", "http_request", "db_query",
            "file_read", "file_write", "api_call"
        ])
        
        # Check EventStatus enum
        assert "EventStatus" in schemas
        status_enum = schemas["EventStatus"]
        assert sorted(status_enum["enum"]) == sorted(["success", "error", "pending"])


class TestEnumExhaustiveness:
    """Test that all enum values are properly handled"""
    
    def test_all_actor_types_valid(self):
        """Verify all ActorType enum values are accepted"""
        for actor_type in ActorType:
            event_data = {
                "event_id": f"test-{actor_type.value}",
                "agent_instance_id": "test-agent",
                "trace_id": "test-trace",
                "actor": actor_type.value,
                "action_type": "tool_call",
                "resource": "test_resource",
                "status": "success"
            }
            response = client.post("/v1/events", json=event_data)
            assert response.status_code == 201, f"Failed for actor: {actor_type.value}"
    
    def test_all_action_types_valid(self):
        """Verify all ActionType enum values are accepted"""
        for action_type in ActionType:
            event_data = {
                "event_id": f"test-{action_type.value}",
                "agent_instance_id": "test-agent",
                "trace_id": "test-trace",
                "actor": "agent",
                "action_type": action_type.value,
                "resource": "test_resource",
                "status": "success"
            }
            response = client.post("/v1/events", json=event_data)
            assert response.status_code == 201, f"Failed for action: {action_type.value}"
    
    def test_all_status_types_valid(self):
        """Verify all EventStatus enum values are accepted"""
        for status in EventStatus:
            event_data = {
                "event_id": f"test-{status.value}",
                "agent_instance_id": "test-agent",
                "trace_id": "test-trace",
                "actor": "agent",
                "action_type": "tool_call",
                "resource": "test_resource",
                "status": status.value
            }
            response = client.post("/v1/events", json=event_data)
            assert response.status_code == 201, f"Failed for status: {status.value}"
    
    def test_invalid_actor_type_rejected(self):
        """Verify invalid actor types are rejected"""
        event_data = {
            "event_id": "test-invalid",
            "agent_instance_id": "test-agent",
            "trace_id": "test-trace",
            "actor": "invalid_actor",
            "action_type": "tool_call",
            "resource": "test_resource",
            "status": "success"
        }
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 422
    
    def test_invalid_action_type_rejected(self):
        """Verify invalid action types are rejected"""
        event_data = {
            "event_id": "test-invalid",
            "agent_instance_id": "test-agent",
            "trace_id": "test-trace",
            "actor": "agent",
            "action_type": "invalid_action",
            "resource": "test_resource",
            "status": "success"
        }
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 422
    
    def test_invalid_status_rejected(self):
        """Verify invalid status values are rejected"""
        event_data = {
            "event_id": "test-invalid",
            "agent_instance_id": "test-agent",
            "trace_id": "test-trace",
            "actor": "agent",
            "action_type": "tool_call",
            "resource": "test_resource",
            "status": "invalid_status"
        }
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 422


class TestPydanticValidation:
    """Test Pydantic model validation"""
    
    def test_required_fields_enforced(self):
        """Verify required fields cannot be omitted"""
        required_fields = [
            "event_id", "agent_instance_id", "trace_id",
            "actor", "action_type", "resource", "status"
        ]
        
        for field_to_omit in required_fields:
            event_data = {
                "event_id": "test-id",
                "agent_instance_id": "test-agent",
                "trace_id": "test-trace",
                "actor": "agent",
                "action_type": "tool_call",
                "resource": "test_resource",
                "status": "success"
            }
            del event_data[field_to_omit]
            
            response = client.post("/v1/events", json=event_data)
            assert response.status_code == 422, f"Should fail when {field_to_omit} is missing"
    
    def test_optional_fields_allowed_null(self):
        """Verify optional fields can be omitted or null"""
        event_data = {
            "event_id": "test-optional",
            "agent_instance_id": "test-agent",
            "trace_id": "test-trace",
            "actor": "agent",
            "action_type": "tool_call",
            "resource": "test_resource",
            "status": "success"
            # latency_ms and metadata omitted
        }
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 201
    
    def test_type_validation(self):
        """Verify type validation works"""
        # Test invalid latency_ms type
        event_data = {
            "event_id": "test-type",
            "agent_instance_id": "test-agent",
            "trace_id": "test-trace",
            "actor": "agent",
            "action_type": "tool_call",
            "resource": "test_resource",
            "status": "success",
            "latency_ms": "not-a-number"  # Should be int
        }
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 422
    
    def test_metadata_dict_validation(self):
        """Verify metadata must be a dictionary"""
        event_data = {
            "event_id": "test-metadata",
            "agent_instance_id": "test-agent",
            "trace_id": "test-trace",
            "actor": "agent",
            "action_type": "tool_call",
            "resource": "test_resource",
            "status": "success",
            "metadata": "not-a-dict"  # Should be dict
        }
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 422


class TestSchemaConsistency:
    """Test schema consistency and backward compatibility"""
    
    def test_enum_count_consistency(self):
        """Verify enum counts match expected values"""
        assert len(ActorType) == 3, "ActorType should have exactly 3 values"
        assert len(ActionType) == 6, "ActionType should have exactly 6 values"
        assert len(EventStatus) == 3, "EventStatus should have exactly 3 values"
    
    def test_pydantic_model_serialization(self):
        """Verify Pydantic models serialize correctly"""
        from datetime import datetime, timezone
        
        # Create a model instance
        event = AuditEvent(
            event_id="test-serialize",
            timestamp=datetime.now(timezone.utc),
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
            latency_ms=100,
            metadata={"key": "value"}
        )
        
        # Serialize to dict
        event_dict = event.model_dump()
        assert "event_id" in event_dict
        assert event_dict["actor"] == "agent"
        assert event_dict["action_type"] == "tool_call"
        assert event_dict["status"] == "success"
    
    def test_response_model_validation(self):
        """Verify response models validate correctly"""
        # Create event first
        event_data = {
            "event_id": "test-response",
            "agent_instance_id": "test-response-agent",
            "trace_id": "test-trace",
            "actor": "agent",
            "action_type": "tool_call",
            "resource": "test_resource",
            "status": "success"
        }
        response = client.post("/v1/events", json=event_data)
        assert response.status_code == 201
        
        # Get events
        response = client.get("/v1/agents/test-response-agent/events")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "events" in data
        assert "total" in data
        assert "agent_instance_id" in data
        assert isinstance(data["events"], list)
        assert isinstance(data["total"], int)
