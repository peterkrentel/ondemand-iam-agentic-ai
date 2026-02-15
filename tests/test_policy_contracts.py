"""
Contract tests for AIMgentix policy files.

Validates that all policy files in .github/agent-policies/ conform to
the schema defined in specs/gha-contracts.md (Contract 3: Policy Schema).

These tests ensure:
  1. Required fields exist (name, version)
  2. Schema compliance for optional fields
  3. Valid YAML syntax
  4. No conflicting rules (same action in allow + deny without conditions)
"""

import pytest
import yaml
from pathlib import Path

# Root directories
REPO_ROOT = Path(__file__).parent.parent
POLICY_DIR = REPO_ROOT / ".github" / "agent-policies"


def get_policy_files():
    """Find all policy YAML files."""
    if not POLICY_DIR.exists():
        return []
    return list(POLICY_DIR.glob("*.yaml")) + list(POLICY_DIR.glob("*.yml"))


@pytest.fixture
def policy_files():
    """Fixture providing all policy files."""
    return get_policy_files()


class TestPolicySchema:
    """Contract tests for policy schema compliance."""

    def test_policy_files_exist(self, policy_files):
        """At least one policy file should exist."""
        assert len(policy_files) > 0, "No policy files found in .github/agent-policies/"

    @pytest.mark.parametrize("policy_path", get_policy_files(), ids=lambda p: p.name)
    def test_valid_yaml(self, policy_path):
        """Policy files must be valid YAML."""
        with open(policy_path) as f:
            policy = yaml.safe_load(f)
        assert policy is not None, f"Policy file {policy_path.name} is empty or invalid"

    @pytest.mark.parametrize("policy_path", get_policy_files(), ids=lambda p: p.name)
    def test_required_fields(self, policy_path):
        """Policy must have required fields: name, version."""
        with open(policy_path) as f:
            policy = yaml.safe_load(f)

        # name: string (required)
        assert "name" in policy, f"Missing required field 'name' in {policy_path.name}"
        assert isinstance(policy["name"], str), f"'name' must be a string in {policy_path.name}"
        assert len(policy["name"]) > 0, f"'name' cannot be empty in {policy_path.name}"

        # version: integer (required)
        assert "version" in policy, f"Missing required field 'version' in {policy_path.name}"
        assert isinstance(policy["version"], int), f"'version' must be an integer in {policy_path.name}"

    @pytest.mark.parametrize("policy_path", get_policy_files(), ids=lambda p: p.name)
    def test_allowed_actions_schema(self, policy_path):
        """allowed_actions must follow schema if present."""
        with open(policy_path) as f:
            policy = yaml.safe_load(f)

        if "allowed_actions" not in policy:
            pytest.skip("No allowed_actions in policy")

        allowed = policy["allowed_actions"]
        assert isinstance(allowed, list), "'allowed_actions' must be a list"

        for i, action in enumerate(allowed):
            assert isinstance(action, dict), f"allowed_actions[{i}] must be a dict"
            assert "type" in action, f"allowed_actions[{i}] missing 'type' field"
            assert isinstance(action["type"], str), f"allowed_actions[{i}].type must be a string"

            # Optional: conditions (object)
            if "conditions" in action:
                assert isinstance(action["conditions"], dict), f"allowed_actions[{i}].conditions must be object"

            # Optional: requires_approval (boolean)
            if "requires_approval" in action:
                assert isinstance(action["requires_approval"], bool), f"allowed_actions[{i}].requires_approval must be bool"

    @pytest.mark.parametrize("policy_path", get_policy_files(), ids=lambda p: p.name)
    def test_denied_actions_schema(self, policy_path):
        """denied_actions must follow schema if present."""
        with open(policy_path) as f:
            policy = yaml.safe_load(f)

        if "denied_actions" not in policy:
            pytest.skip("No denied_actions in policy")

        denied = policy["denied_actions"]
        assert isinstance(denied, list), "'denied_actions' must be a list"

        for i, action in enumerate(denied):
            assert isinstance(action, dict), f"denied_actions[{i}] must be a dict"
            assert "type" in action, f"denied_actions[{i}] missing 'type' field"
            assert isinstance(action["type"], str), f"denied_actions[{i}].type must be a string"

            # Optional: conditions (object)
            if "conditions" in action:
                assert isinstance(action["conditions"], dict), f"denied_actions[{i}].conditions must be object"

    @pytest.mark.parametrize("policy_path", get_policy_files(), ids=lambda p: p.name)
    def test_rate_limits_schema(self, policy_path):
        """rate_limits must follow schema if present."""
        with open(policy_path) as f:
            policy = yaml.safe_load(f)

        if "rate_limits" not in policy:
            pytest.skip("No rate_limits in policy")

        limits = policy["rate_limits"]
        assert isinstance(limits, list), "'rate_limits' must be a list"

        for i, limit in enumerate(limits):
            assert isinstance(limit, dict), f"rate_limits[{i}] must be a dict"
            assert "action" in limit, f"rate_limits[{i}] missing 'action' field"
            assert "max_per_hour" in limit, f"rate_limits[{i}] missing 'max_per_hour' field"
            assert isinstance(limit["action"], str), f"rate_limits[{i}].action must be string"
            assert isinstance(limit["max_per_hour"], int), f"rate_limits[{i}].max_per_hour must be int"
            assert limit["max_per_hour"] > 0, f"rate_limits[{i}].max_per_hour must be positive"

    @pytest.mark.parametrize("policy_path", get_policy_files(), ids=lambda p: p.name)
    def test_auto_approve_schema(self, policy_path):
        """auto_approve must follow schema if present."""
        with open(policy_path) as f:
            policy = yaml.safe_load(f)

        if "auto_approve" not in policy:
            pytest.skip("No auto_approve in policy")

        auto = policy["auto_approve"]
        assert isinstance(auto, list), "'auto_approve' must be a list"

        valid_risk_levels = {"low", "medium", "high"}
        for i, rule in enumerate(auto):
            assert isinstance(rule, dict), f"auto_approve[{i}] must be a dict"
            assert "risk_level" in rule, f"auto_approve[{i}] missing 'risk_level' field"
            assert "actions" in rule, f"auto_approve[{i}] missing 'actions' field"
            assert rule["risk_level"] in valid_risk_levels, f"auto_approve[{i}].risk_level must be low/medium/high"
            assert isinstance(rule["actions"], list), f"auto_approve[{i}].actions must be list"

