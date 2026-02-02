"""
Contract tests for GitHub Actions agent workflows.

These tests validate that agent workflows follow the three-phase pattern
defined in specs/gha-agent-runtime.md and specs/gha-contracts.md.
"""
import glob
import pytest
import yaml
from pathlib import Path

# Get the repository root
REPO_ROOT = Path(__file__).parent.parent
WORKFLOWS_DIR = REPO_ROOT / '.github' / 'workflows'
POLICIES_DIR = REPO_ROOT / '.github' / 'agent-policies'


def get_agent_workflows():
    """Find all agent workflow files."""
    patterns = [
        str(WORKFLOWS_DIR / '*-agent.yml'),
        str(WORKFLOWS_DIR / '*-agent-*.yml'),
    ]
    workflows = []
    for pattern in patterns:
        workflows.extend(glob.glob(pattern))
    return workflows


def get_policy_files():
    """Find all policy files."""
    if not POLICIES_DIR.exists():
        return []
    patterns = [
        str(POLICIES_DIR / '*.yaml'),
        str(POLICIES_DIR / '*.yml'),
    ]
    policies = []
    for pattern in patterns:
        policies.extend(glob.glob(pattern))
    return policies


class TestAgentWorkflowStructure:
    """Tests for agent workflow structure validation."""

    @pytest.fixture
    def agent_workflows(self):
        """Load all agent workflows."""
        workflows = {}
        for path in get_agent_workflows():
            with open(path) as f:
                workflows[path] = yaml.safe_load(f)
        return workflows

    def test_agent_workflows_have_three_phases(self, agent_workflows):
        """All agent workflows must have investigate, approve, act jobs."""
        if not agent_workflows:
            pytest.skip("No agent workflows found")
        
        for path, workflow in agent_workflows.items():
            jobs = workflow.get('jobs', {})
            assert 'investigate' in jobs, f"{path}: Missing 'investigate' job"
            assert 'approve' in jobs, f"{path}: Missing 'approve' job"
            assert 'act' in jobs, f"{path}: Missing 'act' job"

    def test_investigate_job_is_read_only(self, agent_workflows):
        """Investigate job must have read-only permissions."""
        if not agent_workflows:
            pytest.skip("No agent workflows found")
        
        for path, workflow in agent_workflows.items():
            investigate = workflow.get('jobs', {}).get('investigate', {})
            perms = investigate.get('permissions', {})
            
            # Must have explicit permissions
            assert perms, f"{path}: 'investigate' job must have explicit permissions"
            
            # Must not have write-all
            assert perms != 'write-all', f"{path}: 'investigate' job cannot have write-all"
            
            # Must not have contents: write
            if isinstance(perms, dict):
                assert perms.get('contents') != 'write', \
                    f"{path}: 'investigate' job cannot have contents: write"

    def test_approve_job_depends_on_investigate(self, agent_workflows):
        """Approve job must depend on investigate job."""
        if not agent_workflows:
            pytest.skip("No agent workflows found")
        
        for path, workflow in agent_workflows.items():
            approve = workflow.get('jobs', {}).get('approve', {})
            needs = approve.get('needs', [])
            if isinstance(needs, str):
                needs = [needs]
            
            assert 'investigate' in needs, \
                f"{path}: 'approve' job must have 'needs: investigate'"

    def test_act_job_depends_on_approve(self, agent_workflows):
        """Act job must depend on approve job."""
        if not agent_workflows:
            pytest.skip("No agent workflows found")
        
        for path, workflow in agent_workflows.items():
            act = workflow.get('jobs', {}).get('act', {})
            needs = act.get('needs', [])
            if isinstance(needs, str):
                needs = [needs]
            
            assert 'approve' in needs, \
                f"{path}: 'act' job must have 'needs: approve'"

    def test_act_job_has_explicit_permissions(self, agent_workflows):
        """Act job must have explicit permissions."""
        if not agent_workflows:
            pytest.skip("No agent workflows found")
        
        for path, workflow in agent_workflows.items():
            act = workflow.get('jobs', {}).get('act', {})
            perms = act.get('permissions')
            
            assert perms is not None, \
                f"{path}: 'act' job must have explicit permissions"


class TestPolicyContracts:
    """Tests for policy file validation."""

    @pytest.fixture
    def policy_files(self):
        """Load all policy files."""
        policies = {}
        for path in get_policy_files():
            with open(path) as f:
                policies[path] = yaml.safe_load(f)
        return policies

    def test_policies_have_required_fields(self, policy_files):
        """All policies must have name and version."""
        if not policy_files:
            pytest.skip("No policy files found")
        
        for path, policy in policy_files.items():
            assert 'name' in policy, f"{path}: Missing required field 'name'"
            assert 'version' in policy, f"{path}: Missing required field 'version'"

    def test_policy_version_is_integer(self, policy_files):
        """Policy version must be an integer."""
        if not policy_files:
            pytest.skip("No policy files found")
        
        for path, policy in policy_files.items():
            if 'version' in policy:
                assert isinstance(policy['version'], int), \
                    f"{path}: 'version' must be an integer"

    def test_allowed_actions_is_list(self, policy_files):
        """If allowed_actions exists, it must be a list."""
        if not policy_files:
            pytest.skip("No policy files found")
        
        for path, policy in policy_files.items():
            if 'allowed_actions' in policy:
                assert isinstance(policy['allowed_actions'], list), \
                    f"{path}: 'allowed_actions' must be a list"

    def test_denied_actions_is_list(self, policy_files):
        """If denied_actions exists, it must be a list."""
        if not policy_files:
            pytest.skip("No policy files found")
        
        for path, policy in policy_files.items():
            if 'denied_actions' in policy:
                assert isinstance(policy['denied_actions'], list), \
                    f"{path}: 'denied_actions' must be a list"

