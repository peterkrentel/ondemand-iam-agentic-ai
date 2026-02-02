"""
Contract tests for AIMgentix SDK

These tests ensure that:
1. SDK models match backend API contracts
2. Enum values are consistent between SDK and API
3. Data serialization works correctly
4. SDK can communicate with API successfully
"""

from datetime import datetime, timezone

from aimgentix import AuditEvent, ActorType, ActionType, EventStatus


class TestEnumValues:
    """Test that SDK enum values match API expectations"""

    def test_actor_type_values(self):
        """Verify ActorType enum values"""
        assert ActorType.AGENT.value == "agent"
        assert ActorType.HUMAN.value == "human"
        assert ActorType.SYSTEM.value == "system"

        # Verify all expected values exist
        actor_values = {e.value for e in ActorType}
        assert actor_values == {"agent", "human", "system"}

    def test_action_type_values(self):
        """Verify ActionType enum values"""
        assert ActionType.TOOL_CALL.value == "tool_call"
        assert ActionType.HTTP_REQUEST.value == "http_request"
        assert ActionType.DB_QUERY.value == "db_query"
        assert ActionType.FILE_READ.value == "file_read"
        assert ActionType.FILE_WRITE.value == "file_write"
        assert ActionType.API_CALL.value == "api_call"
        assert ActionType.POLICY_CHECK.value == "policy_check"

        # Verify all expected values exist
        action_values = {e.value for e in ActionType}
        assert action_values == {
            "tool_call",
            "http_request",
            "db_query",
            "file_read",
            "file_write",
            "api_call",
            "policy_check",
        }

    def test_event_status_values(self):
        """Verify EventStatus enum values"""
        assert EventStatus.SUCCESS.value == "success"
        assert EventStatus.ERROR.value == "error"
        assert EventStatus.PENDING.value == "pending"
        assert EventStatus.DENIED.value == "denied"

        # Verify all expected values exist
        status_values = {e.value for e in EventStatus}
        assert status_values == {"success", "error", "pending", "denied"}

    def test_enum_counts(self):
        """Verify enum counts match expected values"""
        assert len(ActorType) == 3, "ActorType should have exactly 3 values"
        assert len(ActionType) == 7, "ActionType should have exactly 7 values"
        assert len(EventStatus) == 4, "EventStatus should have exactly 4 values"


class TestAuditEventContract:
    """Test AuditEvent dataclass structure and serialization"""

    def test_required_fields(self):
        """Verify all required fields are present"""
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        # Verify required fields exist
        assert event.agent_instance_id == "test-agent"
        assert event.trace_id == "test-trace"
        assert event.actor == ActorType.AGENT
        assert event.action_type == ActionType.TOOL_CALL
        assert event.resource == "test_resource"
        assert event.status == EventStatus.SUCCESS

    def test_auto_generated_fields(self):
        """Verify auto-generated fields are created"""
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        # Verify auto-generated fields
        assert event.event_id is not None
        assert isinstance(event.event_id, str)
        assert len(event.event_id) > 0

        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    def test_optional_fields(self):
        """Verify optional fields work correctly"""
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
            latency_ms=100,
            metadata={"key": "value"},
        )

        assert event.latency_ms == 100
        assert event.metadata == {"key": "value"}

    def test_default_metadata(self):
        """Verify metadata defaults to empty dict"""
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        assert event.metadata == {}


class TestSerialization:
    """Test event serialization for API communication"""

    def test_to_dict_basic(self):
        """Verify basic to_dict serialization"""
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        data = event.to_dict()

        # Verify structure
        assert isinstance(data, dict)
        assert "event_id" in data
        assert "timestamp" in data
        assert "agent_instance_id" in data
        assert "trace_id" in data
        assert "actor" in data
        assert "action_type" in data
        assert "resource" in data
        assert "status" in data

    def test_to_dict_enum_conversion(self):
        """Verify enums are converted to strings"""
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        data = event.to_dict()

        # Verify enum values are strings
        assert data["actor"] == "agent"
        assert data["action_type"] == "tool_call"
        assert data["status"] == "success"
        assert isinstance(data["actor"], str)
        assert isinstance(data["action_type"], str)
        assert isinstance(data["status"], str)

    def test_to_dict_timestamp_format(self):
        """Verify timestamp is ISO8601 formatted"""
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        data = event.to_dict()

        # Verify timestamp is a string in ISO8601 format
        assert isinstance(data["timestamp"], str)
        # Should be able to parse back
        parsed = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_to_dict_with_optional_fields(self):
        """Verify optional fields are included when present"""
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
            latency_ms=250,
            metadata={"tool": "search", "query": "[REDACTED]"},
        )

        data = event.to_dict()

        assert data["latency_ms"] == 250
        assert data["metadata"] == {"tool": "search", "query": "[REDACTED]"}

    def test_to_dict_json_serializable(self):
        """Verify to_dict output is JSON serializable"""
        import json

        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
            latency_ms=100,
            metadata={"key": "value"},
        )

        data = event.to_dict()

        # Should not raise an exception
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["agent_instance_id"] == "test-agent"


class TestEnumExhaustiveness:
    """Test all enum values can be used"""

    def test_all_actor_types_creatable(self):
        """Verify events can be created with all ActorType values"""
        for actor in ActorType.__members__.values():
            event = AuditEvent(
                agent_instance_id="test-agent",
                trace_id="test-trace",
                actor=actor,
                action_type=ActionType.TOOL_CALL,
                resource="test_resource",
                status=EventStatus.SUCCESS,
            )
            assert event.actor == actor
            data = event.to_dict()
            assert data["actor"] == actor.value

    def test_all_action_types_creatable(self):
        """Verify events can be created with all ActionType values"""
        for action in ActionType.__members__.values():
            event = AuditEvent(
                agent_instance_id="test-agent",
                trace_id="test-trace",
                actor=ActorType.AGENT,
                action_type=action,
                resource="test_resource",
                status=EventStatus.SUCCESS,
            )
            assert event.action_type == action
            data = event.to_dict()
            assert data["action_type"] == action.value

    def test_all_status_types_creatable(self):
        """Verify events can be created with all EventStatus values"""
        for status in EventStatus.__members__.values():
            event = AuditEvent(
                agent_instance_id="test-agent",
                trace_id="test-trace",
                actor=ActorType.AGENT,
                action_type=ActionType.TOOL_CALL,
                resource="test_resource",
                status=status,
            )
            assert event.status == status
            data = event.to_dict()
            assert data["status"] == status.value


class TestDataIntegrity:
    """Test data integrity and type safety"""

    def test_event_id_uniqueness(self):
        """Verify each event gets a unique ID"""
        event1 = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        event2 = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        assert event1.event_id != event2.event_id

    def test_timestamp_is_utc(self):
        """Verify timestamps are in UTC"""
        event = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        # Timestamp should have timezone info
        assert event.timestamp.tzinfo is not None
        # Should be UTC
        assert event.timestamp.tzinfo == timezone.utc

    def test_metadata_immutability(self):
        """Verify metadata dict is not shared between instances"""
        event1 = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        event2 = AuditEvent(
            agent_instance_id="test-agent",
            trace_id="test-trace",
            actor=ActorType.AGENT,
            action_type=ActionType.TOOL_CALL,
            resource="test_resource",
            status=EventStatus.SUCCESS,
        )

        # Modify one metadata dict
        event1.metadata["test"] = "value"

        # Should not affect the other
        assert "test" not in event2.metadata
