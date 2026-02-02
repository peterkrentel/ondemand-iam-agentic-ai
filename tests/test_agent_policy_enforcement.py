"""
Agent Policy Enforcement Tests

These tests ensure that agent implementations ACTUALLY enforce policies
as defined in specs/gha-agent-runtime.md.

This is the guardrail that prevents the spec from being ignored.

Per spec, agents MUST:
1. Load policy from .github/agent-policies/<agent-name>.yaml
2. Check policy BEFORE every action
3. Follow evaluation order: denied → rate_limits → allowed → requires_approval
4. Emit policy_check audit events
5. Respect policy decisions (deny if policy says no)
"""

import re
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"


def get_agent_files():
    """Find all agent Python files."""
    agents = []
    for agent_dir in AGENTS_DIR.iterdir():
        if agent_dir.is_dir():
            agent_file = agent_dir / "agent.py"
            if agent_file.exists():
                agents.append(agent_file)
    return agents


def get_agent_source(agent_path: Path) -> str:
    """Read agent source code."""
    return agent_path.read_text()


class TestAgentLoadsPolicyFile:
    """Verify agents load their policy file."""

    @pytest.fixture
    def agent_files(self):
        return get_agent_files()

    def test_agents_import_yaml(self, agent_files):
        """Agents must import yaml to load policy files."""
        if not agent_files:
            pytest.skip("No agent files found")

        for agent_path in agent_files:
            source = get_agent_source(agent_path)
            assert (
                "import yaml" in source or "from yaml" in source
            ), f"{agent_path}: Agent must import yaml to load policy files"

    def test_agents_reference_policy_path(self, agent_files):
        """Agents must reference the policy file path."""
        if not agent_files:
            pytest.skip("No agent files found")

        for agent_path in agent_files:
            source = get_agent_source(agent_path)
            # Must reference .github/agent-policies/ somewhere
            assert (
                "agent-policies" in source or "POLICY_PATH" in source
            ), f"{agent_path}: Agent must reference policy file path"

    def test_agents_have_policy_enforcer(self, agent_files):
        """Agents must have a PolicyEnforcer or equivalent."""
        if not agent_files:
            pytest.skip("No agent files found")

        for agent_path in agent_files:
            source = get_agent_source(agent_path)
            # Must have policy enforcement class/function
            has_enforcer = (
                "PolicyEnforcer" in source
                or "policy_check" in source
                or "_check_policy" in source
                or "check_policy" in source
            )
            assert has_enforcer, f"{agent_path}: Agent must have policy enforcement (PolicyEnforcer or check_policy)"


class TestAgentChecksPolicyBeforeActions:
    """Verify agents check policy before AWS/external operations."""

    @pytest.fixture
    def agent_files(self):
        return get_agent_files()

    def test_agents_check_policy_before_aws_calls(self, agent_files):
        """Agents must check policy before AWS API calls."""
        if not agent_files:
            pytest.skip("No agent files found")

        for agent_path in agent_files:
            source = get_agent_source(agent_path)

            # Find AWS operations (boto3 calls)
            aws_patterns = [
                r"\.create_bucket\(",
                r"\.delete_bucket\(",
                r"\.put_object\(",
                r"\.delete_object\(",
                r"\.put_bucket_lifecycle",
            ]

            for pattern in aws_patterns:
                matches = list(re.finditer(pattern, source))
                for match in matches:
                    # Get the 1500 chars before this AWS call
                    # (enough to cover config setup between policy check and call)
                    start = max(0, match.start() - 1500)
                    context_before = source[start : match.start()]  # noqa: E203

                    # Must have policy check before AWS call
                    has_policy_check = (
                        "_require_policy" in context_before
                        or "_check_policy" in context_before
                        or "policy.check" in context_before
                        or "PolicyEnforcer" in context_before
                    )

                    assert has_policy_check, (
                        f"{agent_path}: AWS call '{pattern}' at position {match.start()} "
                        f"must have policy check before it. "
                        f"See specs/gha-agent-runtime.md for requirements."
                    )


class TestAgentEmitsPolicyEvents:
    """Verify agents emit audit events for policy decisions."""

    @pytest.fixture
    def agent_files(self):
        return get_agent_files()

    def test_agents_emit_policy_check_events(self, agent_files):
        """Agents must emit POLICY_CHECK audit events."""
        if not agent_files:
            pytest.skip("No agent files found")

        for agent_path in agent_files:
            source = get_agent_source(agent_path)
            assert (
                "POLICY_CHECK" in source or "policy_check" in source
            ), f"{agent_path}: Agent must emit POLICY_CHECK audit events"

    def test_agents_handle_denied_status(self, agent_files):
        """Agents must handle DENIED status for policy violations."""
        if not agent_files:
            pytest.skip("No agent files found")

        for agent_path in agent_files:
            source = get_agent_source(agent_path)
            has_denied = "DENIED" in source or "denied" in source.lower()
            assert has_denied, f"{agent_path}: Agent must handle DENIED status for policy violations"
