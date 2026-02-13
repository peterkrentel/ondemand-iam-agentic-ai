"""
Contract Tests for GitHub Actions Agent Runtime

These tests validate that the workflow implementation matches the spec:
specs/github-actions-agent-runtime.md

Tests:
- Workflow structure (jobs, dependencies, permissions)
- Required inputs/outputs
- Agent runner script behavior
- Audit trail integration
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


class TestWorkflowContract(unittest.TestCase):
    """Test workflow file structure and contracts"""

    @classmethod
    def setUpClass(cls):
        """Load workflow file"""
        workflow_path = Path(__file__).parent.parent / '.github' / 'workflows' / 'agent-investigate-act.yml'
        with open(workflow_path) as f:
            cls.workflow = yaml.safe_load(f)

    def test_workflow_has_required_inputs(self):
        """Workflow must accept required inputs per spec"""
        required_inputs = ['trigger_source', 'trace_id', 'resource']

        # Handle 'on' key which might be renamed by YAML parser
        on_key = self.workflow.get('on') or self.workflow.get(True)
        if not on_key:
            self.fail("Workflow missing 'on' section")

        inputs = on_key['workflow_dispatch']['inputs']

        for input_name in required_inputs:
            self.assertIn(input_name, inputs, f"Missing required input: {input_name}")
            self.assertTrue(
                inputs[input_name].get('required', False),
                f"Input {input_name} must be required"
            )

    def test_workflow_has_optional_inputs(self):
        """Workflow should accept optional inputs per spec"""
        optional_inputs = ['action_context']

        # Handle 'on' key which might be renamed by YAML parser
        on_key = self.workflow.get('on') or self.workflow.get(True)
        if not on_key:
            self.fail("Workflow missing 'on' section")

        inputs = on_key['workflow_dispatch']['inputs']

        for input_name in optional_inputs:
            self.assertIn(input_name, inputs, f"Missing optional input: {input_name}")
            self.assertFalse(
                inputs[input_name].get('required', True),
                f"Input {input_name} should be optional"
            )

    def test_workflow_has_three_main_jobs(self):
        """Workflow must have investigate, approve, act jobs per spec"""
        required_jobs = ['investigate', 'approve', 'act']
        jobs = self.workflow['jobs']

        for job_name in required_jobs:
            self.assertIn(job_name, jobs, f"Missing required job: {job_name}")

    def test_investigate_job_has_read_only_permissions(self):
        """Investigate job must have read-only permissions per spec"""
        investigate = self.workflow['jobs']['investigate']
        permissions = investigate.get('permissions', {})

        # Should only have contents: read
        self.assertEqual(
            permissions.get('contents'),
            'read',
            "Investigate job must have 'contents: read' permission"
        )

        # Should not have write permissions
        for key, value in permissions.items():
            self.assertNotEqual(
                value,
                'write',
                f"Investigate job must not have write permission: {key}"
            )

    def test_investigate_job_produces_required_outputs(self):
        """Investigate job must produce required outputs per spec"""
        required_outputs = [
            'recommendation',
            'safe_to_proceed',
            'confidence_score',
            'investigation_summary'
        ]
        investigate = self.workflow['jobs']['investigate']
        outputs = investigate.get('outputs', {})

        for output_name in required_outputs:
            self.assertIn(
                output_name,
                outputs,
                f"Missing required output: {output_name}"
            )

    def test_approve_job_depends_on_investigate(self):
        """Approve job must depend on investigate job per spec"""
        approve = self.workflow['jobs']['approve']
        needs = approve.get('needs')

        self.assertEqual(
            needs,
            'investigate',
            "Approve job must depend on investigate job"
        )

    def test_approve_job_uses_environment_protection(self):
        """Approve job must use environment protection per spec"""
        approve = self.workflow['jobs']['approve']
        environment = approve.get('environment')

        self.assertIsNotNone(
            environment,
            "Approve job must use environment protection"
        )

        # Environment should be a dict with name
        if isinstance(environment, dict):
            self.assertIn('name', environment, "Environment must have a name")
            env_name = environment['name']
        else:
            env_name = environment

        self.assertEqual(
            env_name,
            'agent-approval',
            "Environment name should be 'agent-approval'"
        )

    def test_act_job_has_elevated_permissions(self):
        """Act job must have elevated permissions per spec"""
        act = self.workflow['jobs']['act']
        permissions = act.get('permissions', {})

        # Should have at least one write permission
        has_write = any(
            value == 'write'
            for value in permissions.values()
        )
        self.assertTrue(
            has_write,
            "Act job must have at least one write permission"
        )

    def test_workflow_creates_required_artifacts(self):
        """Workflow must create required artifacts per spec"""
        required_artifacts = [
            'investigation-report',
            'audit-trace-id',
            'action-result'
        ]

        # Check all jobs for artifact uploads
        found_artifacts = set()
        for job_name, job in self.workflow['jobs'].items():
            steps = job.get('steps', [])
            for step in steps:
                if step.get('uses', '').startswith('actions/upload-artifact'):
                    artifact_name = step.get('with', {}).get('name')
                    if artifact_name:
                        found_artifacts.add(artifact_name)

        for artifact in required_artifacts:
            self.assertIn(
                artifact,
                found_artifacts,
                f"Missing required artifact: {artifact}"
            )


class TestAgentRunnerScript(unittest.TestCase):
    """Test agent_runner.py script behavior"""

    @classmethod
    def setUpClass(cls):
        """Locate agent_runner.py"""
        cls.script_path = Path(__file__).parent.parent / 'agent_runner.py'
        if not cls.script_path.exists():
            raise unittest.SkipTest("agent_runner.py not found")

    def test_script_has_investigate_command(self):
        """Script must support investigate command"""
        result = subprocess.run(
            ['python', str(self.script_path), '--help'],
            capture_output=True,
            text=True
        )
        self.assertIn('investigate', result.stdout)

    def test_script_has_act_command(self):
        """Script must support act command"""
        result = subprocess.run(
            ['python', str(self.script_path), '--help'],
            capture_output=True,
            text=True
        )
        self.assertIn('act', result.stdout)

    def test_investigate_requires_resource(self):
        """Investigate command must require --resource"""
        result = subprocess.run(
            ['python', str(self.script_path), 'investigate'],
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('resource', result.stderr.lower())

    def test_investigate_produces_json_output(self):
        """Investigate command must produce valid JSON output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'investigation-report.json'
            result = subprocess.run(
                [
                    'python', str(self.script_path),
                    'investigate',
                    '--resource', 'test-resource',
                    '--trace-id', 'test-trace',
                    '--output-file', str(output_file)
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
            self.assertTrue(output_file.exists(), "Output file not created")
            with open(output_file) as f:
                data = json.load(f)
            required_fields = [
                'timestamp', 'resource', 'status', 'risk_level',
                'recommendation', 'confidence', 'safe_to_proceed'
            ]
            for field in required_fields:
                self.assertIn(field, data, f"Missing field in output: {field}")

    def test_act_produces_json_output(self):
        """Act command must produce valid JSON output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'action-result.json'
            result = subprocess.run(
                [
                    'python', str(self.script_path),
                    'act',
                    '--resource', 'test-resource',
                    '--action', 'restart',
                    '--trace-id', 'test-trace',
                    '--output-file', str(output_file)
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
            self.assertTrue(output_file.exists(), "Output file not created")
            with open(output_file) as f:
                data = json.load(f)
            required_fields = [
                'timestamp', 'resource', 'action', 'status', 'latency_ms'
            ]
            for field in required_fields:
                self.assertIn(field, data, f"Missing field in output: {field}")


class TestSpecCompliance(unittest.TestCase):
    """Test overall spec compliance"""

    def test_spec_file_exists(self):
        """Spec file must exist"""
        spec_path = Path(__file__).parent.parent / 'specs' / 'github-actions-agent-runtime.md'
        self.assertTrue(spec_path.exists(), "Spec file not found")

    def test_workflow_file_references_spec(self):
        """Workflow file should reference the spec"""
        workflow_path = Path(__file__).parent.parent / '.github' / 'workflows' / 'agent-investigate-act.yml'
        with open(workflow_path) as f:
            content = f.read()
        self.assertIn(
            'specs/github-actions-agent-runtime.md',
            content,
            "Workflow should reference the spec file"
        )

    def test_documentation_exists(self):
        """Documentation files must exist"""
        docs = [
            'docs/GITHUB_ACTIONS_RUNTIME.md',
            'docs/SETUP_GUIDE.md'
        ]
        base_path = Path(__file__).parent.parent
        for doc in docs:
            doc_path = base_path / doc
            self.assertTrue(doc_path.exists(), f"Missing documentation: {doc}")


if __name__ == '__main__':
    unittest.main()
