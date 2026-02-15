#!/usr/bin/env python3
"""
S3 Lifecycle Demo Agent

Demonstrates the investigate → approve → act pattern with AIMgentix policy enforcement.

⚠️  THIS AGENT ONLY RUNS IN GITHUB ACTIONS - NOT LOCALLY.

Policy enforcement follows specs/gha-agent-runtime.md:
  1. Check denied_actions - if match, DENY
  2. Check rate_limits - if exceeded, DENY
  3. Check allowed_actions - if no match, DENY
  4. Check requires_approval - if true, require gate
  5. Otherwise, ALLOW

Usage (in GitHub Actions only):
    python agent.py investigate  # Analyze and propose action
    python agent.py act          # Execute the approved action
    python agent.py cleanup      # Clean up demo resources
"""

import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

import yaml


def require_github_actions():
    """Ensure this script only runs in GitHub Actions."""
    if os.getenv("GITHUB_ACTIONS") != "true":
        print("❌ ERROR: This agent only runs in GitHub Actions, not locally.")
        print("")
        print("Why? Security:")
        print("  - AWS credentials should come from GitHub OIDC, not your laptop")
        print("  - All actions must have full audit trail in GitHub Actions logs")
        print("  - Approval gates only work in GitHub Actions workflows")
        print("")
        print("To run this agent:")
        print("  1. Push to the repository")
        print("  2. Trigger the workflow via GitHub Actions UI")
        print("  3. Or use: gh workflow run s3-lifecycle-agent.yml")
        sys.exit(1)


# Guard: Only run in GitHub Actions
require_github_actions()

# Now safe to import AWS SDK (after guard check)
import boto3  # noqa: E402

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "sdk"))

# Import SDK components including policy engine
from aimgentix import (  # noqa: E402
    AuditClient,
    AuditEvent,
    ActorType,
    ActionType,
    EventStatus,
    PolicyEnforcer,
    PolicyDecision,
    PolicyViolation,
)


class S3LifecycleAgent:
    """
    Agent that manages S3 bucket lifecycle for demonstration.

    All actions are checked against AIMgentix policy BEFORE execution.
    Policy file: .github/agent-policies/s3-lifecycle.yaml
    """

    # Policy file location (relative to repo root)
    POLICY_PATH = ".github/agent-policies/s3-lifecycle.yaml"

    def __init__(self):
        # Find repo root (where .github/ lives)
        self.repo_root = self._find_repo_root()

        # Load policy - this is the AIMgentix permission layer
        policy_path = self.repo_root / self.POLICY_PATH
        print(f"📜 Loading policy: {policy_path}")
        self.policy = PolicyEnforcer(policy_path)
        print(f"   Policy: {self.policy.name} v{self.policy.version}")
        print(f"   Allowed actions: {len(self.policy.allowed_actions)}")
        print(f"   Denied actions: {len(self.policy.denied_actions)}")

        # Initialize audit client
        self.audit = AuditClient(
            api_url=os.getenv("AIMGENTIX_API_URL", "http://localhost:8000"),
            verify_ssl=os.getenv("AIMGENTIX_VERIFY_SSL", "true").lower() == "true",
        )

        # Set trace ID from GHA or generate new one
        run_id = os.getenv("GITHUB_RUN_ID", str(uuid.uuid4())[:8])
        run_attempt = os.getenv("GITHUB_RUN_ATTEMPT", "1")
        self.trace_id = f"{run_id}-{run_attempt}"

        # Set agent ID from GHA or use default
        workflow = os.getenv("GITHUB_WORKFLOW", "s3-lifecycle")
        job = os.getenv("GITHUB_JOB", "local")
        self.agent_id = f"{workflow}-{job}"

        # Initialize S3 client
        self.s3 = boto3.client("s3")
        self.region = os.getenv("AWS_REGION", "us-east-1")

    def _find_repo_root(self) -> Path:
        """Find the repository root (where .github/ lives)."""
        # Start from this file and walk up
        current = Path(__file__).parent
        for _ in range(10):  # Max 10 levels up
            if (current / ".github").exists():
                return current
            current = current.parent
        # Fallback to GITHUB_WORKSPACE or current dir
        return Path(os.getenv("GITHUB_WORKSPACE", "."))

    def _check_policy(self, action_type: str, **context) -> PolicyDecision:
        """
        Check policy and emit audit event for the decision.

        This is the core of AIMgentix - every action is checked against policy.
        """
        decision = self.policy.check(action_type, **context)

        # Emit policy decision event
        self._emit_event(
            ActionType.POLICY_CHECK,
            f"policy:{action_type}",
            EventStatus.SUCCESS if decision.allowed else EventStatus.DENIED,
            metadata={
                "action_type": action_type,
                "context": context,
                "decision": {
                    "allowed": decision.allowed,
                    "reason": decision.reason,
                    "requires_approval": decision.requires_approval,
                    "matched_rule": decision.matched_rule,
                },
            },
        )

        if decision.allowed:
            print(f"   ✅ Policy allows: {action_type}")
        else:
            print(f"   ❌ Policy denies: {action_type} - {decision.reason}")

        return decision

    def _require_policy(self, action_type: str, **context) -> PolicyDecision:
        """Check policy and raise if denied."""
        decision = self._check_policy(action_type, **context)
        if not decision.allowed:
            raise PolicyViolation(decision)
        return decision

    def _emit_event(
        self, action_type: ActionType, resource: str, status: EventStatus, latency_ms: int = None, metadata: dict = None
    ):
        """Emit an audit event."""
        event = AuditEvent(
            agent_instance_id=self.agent_id,
            trace_id=self.trace_id,
            actor=ActorType.SYSTEM,
            action_type=action_type,
            resource=resource,
            status=status,
            latency_ms=latency_ms,
            metadata={
                **(metadata or {}),
                "gha": {
                    "run_id": os.getenv("GITHUB_RUN_ID"),
                    "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
                    "workflow": os.getenv("GITHUB_WORKFLOW"),
                    "job": os.getenv("GITHUB_JOB"),
                    "repository": os.getenv("GITHUB_REPOSITORY"),
                    "sha": os.getenv("GITHUB_SHA"),
                    "ref": os.getenv("GITHUB_REF"),
                },
            },
        )
        self.audit.capture(event)

    def _write_output(self, key: str, value: str):
        """Write output to GitHub Actions."""
        output_file = os.getenv("GITHUB_OUTPUT")
        if output_file:
            with open(output_file, "a") as f:
                f.write(f"{key}={value}\n")
        print(f"OUTPUT: {key}={value}")

    def investigate(self) -> dict:
        """
        INVESTIGATE phase: Analyze current state and propose action.

        This phase is READ-ONLY. It checks existing buckets and proposes
        what action to take. All actions are validated against AIMgentix policy.
        """
        print("🔍 INVESTIGATE: Analyzing S3 state...")
        print("")

        findings = []
        proposed_action = None
        risk_level = "low"

        # Check policy allows ListBuckets (read-only action)
        print("📜 Checking policy for s3:ListBuckets...")
        list_decision = self._check_policy("s3:ListBuckets")
        if not list_decision.allowed:
            findings.append(
                {
                    "type": "policy_violation",
                    "message": f"Policy denies s3:ListBuckets: {list_decision.reason}",
                    "severity": "error",
                }
            )
            risk_level = "high"

        # Check existing demo buckets (if policy allows)
        demo_buckets = []
        if list_decision.allowed:
            start = datetime.now()
            try:
                response = self.s3.list_buckets()
                latency = int((datetime.now() - start).total_seconds() * 1000)

                self._emit_event(
                    ActionType.API_CALL,
                    "s3:ListBuckets",
                    EventStatus.SUCCESS,
                    latency_ms=latency,
                    metadata={"bucket_count": len(response["Buckets"])},
                )

                # Find buckets matching policy's allowed pattern
                # We look for aimgentix-demo-* based on policy's bucket_name_pattern
                demo_buckets = [
                    b["Name"] for b in response["Buckets"] if fnmatch.fnmatch(b["Name"], "aimgentix-demo-*")
                ]

                findings.append(
                    {
                        "type": "observation",
                        "message": f"Found {len(demo_buckets)} existing demo buckets",
                        "severity": "info",
                        "data": {"buckets": demo_buckets},
                    }
                )

            except Exception as e:
                self._emit_event(ActionType.API_CALL, "s3:ListBuckets", EventStatus.ERROR, metadata={"error": str(e)})
                findings.append({"type": "error", "message": f"Failed to list buckets: {e}", "severity": "error"})
                risk_level = "high"

        # Propose action based on findings
        if risk_level != "high":
            # Generate bucket name matching policy pattern
            bucket_name = f"aimgentix-demo-{uuid.uuid4().hex[:8]}"

            # Check if policy would allow this action BEFORE proposing it
            print("")
            print("📜 Checking policy for proposed s3:CreateBucket...")
            create_decision = self._check_policy("s3:CreateBucket", bucket_name=bucket_name, region=self.region)

            if create_decision.allowed:
                proposed_action = {
                    "type": "s3:CreateBucket",
                    "parameters": {"bucket_name": bucket_name, "region": self.region},
                    "reason": "Create demo bucket for lifecycle demonstration",
                    "reversible": True,
                    "policy_decision": {"allowed": True, "requires_approval": create_decision.requires_approval},
                }

                if create_decision.requires_approval:
                    risk_level = "medium"
                    findings.append(
                        {"type": "policy_note", "message": "Action requires approval per policy", "severity": "info"}
                    )
            else:
                # Policy would deny this action
                risk_level = "high"
                findings.append(
                    {
                        "type": "policy_violation",
                        "message": f"Policy denies s3:CreateBucket: {create_decision.reason}",
                        "severity": "error",
                        "data": {"bucket_name": bucket_name, "region": self.region},
                    }
                )

        # Build findings document
        findings_doc = {
            "schema_version": "1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "trace_id": self.trace_id,
            "agent_id": self.agent_id,
            "findings": findings,
            "proposed_action": proposed_action,
            "risk_assessment": {"level": risk_level, "factors": self._get_risk_factors(proposed_action)},
        }

        # Write outputs for GitHub Actions
        self._write_output("risk_level", risk_level)
        self._write_output("proposed_action", json.dumps(proposed_action) if proposed_action else "{}")
        self._write_output("findings_summary", f"Found {len(findings)} findings, risk={risk_level}")

        # Save findings artifact
        Path("findings.json").write_text(json.dumps(findings_doc, indent=2))
        print("📄 Saved findings.json")

        # Emit final investigation event
        self._emit_event(
            ActionType.TOOL_CALL,
            "investigate",
            EventStatus.SUCCESS,
            metadata={
                "phase": "investigate",
                "findings_count": len(findings),
                "risk_level": risk_level,
                "proposed_action_type": proposed_action["type"] if proposed_action else None,
            },
        )

        self.audit.flush()
        print(f"✅ Investigation complete. Risk level: {risk_level}")
        return findings_doc

    def _get_risk_factors(self, action: dict) -> list:
        """Determine risk factors for an action."""
        factors = []
        if not action:
            return ["no_action_proposed"]

        action_type = action.get("type", "")

        if action.get("reversible"):
            factors.append("reversible")
        else:
            factors.append("irreversible")

        if "Delete" in action_type:
            factors.append("destructive")
        elif "Create" in action_type:
            factors.append("new_resource")

        # Check if bucket matches demo pattern (from policy)
        bucket_name = str(action.get("parameters", {}).get("bucket_name", ""))
        if fnmatch.fnmatch(bucket_name, "aimgentix-demo-*"):
            factors.append("demo_resource")
        else:
            factors.append("non_demo_resource")

        return factors

    def act(self) -> dict:
        """
        ACT phase: Execute the approved action.

        All actions are checked against AIMgentix policy BEFORE execution.
        This phase performs the actual S3 operations:
        1. Create bucket (policy checked)
        2. Set lifecycle policy (policy checked)
        3. Upload test object (policy checked)
        """
        print("🚀 ACT: Executing approved action...")
        print("")

        # Load proposed action from findings
        findings_path = Path("findings.json")
        if not findings_path.exists():
            # Try to get from downloaded artifact
            findings_path = Path("findings/findings.json")

        if not findings_path.exists():
            print("❌ No findings.json found. Run investigate first.")
            return {"success": False, "error": "No findings"}

        findings = json.loads(findings_path.read_text())
        action = findings.get("proposed_action")

        if not action:
            print("❌ No action proposed in findings.")
            return {"success": False, "error": "No action proposed"}

        results = {
            "schema_version": "1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "trace_id": self.trace_id,
            "agent_id": self.agent_id,
            "action_taken": action,
            "success": True,
            "details": {},
            "audit_events": [],
            "policy_decisions": [],
        }

        bucket_name = action["parameters"]["bucket_name"]
        region = action["parameters"]["region"]

        try:
            # Step 1: Create bucket - CHECK POLICY FIRST
            print(f"📦 Creating bucket: {bucket_name}")
            print("📜 Checking policy for s3:CreateBucket...")
            self._require_policy("s3:CreateBucket", bucket_name=bucket_name, region=region)
            results["policy_decisions"].append({"action": "s3:CreateBucket", "allowed": True})

            start = datetime.now()
            create_config = {}
            if region != "us-east-1":
                create_config["CreateBucketConfiguration"] = {"LocationConstraint": region}

            self.s3.create_bucket(Bucket=bucket_name, **create_config)
            latency = int((datetime.now() - start).total_seconds() * 1000)

            self._emit_event(
                ActionType.API_CALL,
                f"s3:CreateBucket:{bucket_name}",
                EventStatus.SUCCESS,
                latency_ms=latency,
                metadata={"bucket_name": bucket_name, "region": region},
            )
            results["details"]["bucket_created"] = bucket_name
            print("  ✅ Bucket created")

            # Step 2: Set lifecycle policy - CHECK POLICY FIRST
            print("")
            print("⏰ Setting lifecycle policy...")
            print("📜 Checking policy for s3:PutLifecycleConfiguration...")
            self._require_policy("s3:PutLifecycleConfiguration", bucket_name=bucket_name)
            results["policy_decisions"].append({"action": "s3:PutLifecycleConfiguration", "allowed": True})

            start = datetime.now()
            lifecycle_config = {
                "Rules": [
                    {
                        "ID": "demo-lifecycle-rule",
                        "Status": "Enabled",
                        "Filter": {"Prefix": ""},
                        "Transitions": [{"Days": 1, "StorageClass": "GLACIER"}],  # AWS minimum
                        "Expiration": {"Days": 2},  # Delete after 2 days
                    }
                ]
            }

            self.s3.put_bucket_lifecycle_configuration(Bucket=bucket_name, LifecycleConfiguration=lifecycle_config)
            latency = int((datetime.now() - start).total_seconds() * 1000)

            self._emit_event(
                ActionType.API_CALL,
                f"s3:PutLifecycleConfiguration:{bucket_name}",
                EventStatus.SUCCESS,
                latency_ms=latency,
                metadata={"lifecycle_rules": lifecycle_config["Rules"]},
            )
            results["details"]["lifecycle_configured"] = True
            print("  ✅ Lifecycle policy set (transition to Glacier: 1 day, expire: 2 days)")

            # Step 3: Upload test object - CHECK POLICY FIRST
            print("")
            print("📄 Uploading test object...")
            test_object_key = f"test-object-{uuid.uuid4().hex[:8]}.txt"
            print("📜 Checking policy for s3:PutObject...")
            self._require_policy("s3:PutObject", bucket_name=bucket_name, key=test_object_key)
            results["policy_decisions"].append({"action": "s3:PutObject", "allowed": True})

            start = datetime.now()
            test_content = f"AIMgentix Demo Object\nCreated: {datetime.utcnow().isoformat()}\nTrace: {self.trace_id}"

            self.s3.put_object(Bucket=bucket_name, Key=test_object_key, Body=test_content.encode())
            latency = int((datetime.now() - start).total_seconds() * 1000)

            self._emit_event(
                ActionType.API_CALL,
                f"s3:PutObject:{bucket_name}/{test_object_key}",
                EventStatus.SUCCESS,
                latency_ms=latency,
                metadata={"key": test_object_key, "size_bytes": len(test_content)},
            )
            results["details"]["object_uploaded"] = test_object_key
            print(f"  ✅ Object uploaded: {test_object_key}")

        except PolicyViolation as pv:
            results["success"] = False
            results["details"]["error"] = f"Policy violation: {pv.decision.reason}"
            results["policy_decisions"].append({"action": "unknown", "allowed": False, "reason": pv.decision.reason})
            print(f"  ❌ Policy violation: {pv.decision.reason}")

        except Exception as e:
            results["success"] = False
            results["details"]["error"] = str(e)

            self._emit_event(ActionType.API_CALL, f"s3:{action['type']}", EventStatus.ERROR, metadata={"error": str(e)})
            print(f"  ❌ Error: {e}")

        # Emit final act event
        self._emit_event(
            ActionType.TOOL_CALL,
            "act",
            EventStatus.SUCCESS if results["success"] else EventStatus.ERROR,
            metadata={
                "phase": "act",
                "action_type": action["type"],
                "success": results["success"],
                "bucket_name": bucket_name,
            },
        )

        # Save results artifact
        Path("results.json").write_text(json.dumps(results, indent=2))
        print("📄 Saved results.json")

        self.audit.flush()
        self.audit.close()

        print(f"✅ Action complete. Success: {results['success']}")
        return results

    def cleanup(self) -> dict:
        """
        CLEANUP: Remove demo resources.

        All delete operations are checked against AIMgentix policy BEFORE execution.
        Deletes all buckets matching the demo pattern (aimgentix-demo-*).
        """
        print("🧹 CLEANUP: Removing demo resources...")
        print("")

        deleted = []
        errors = []
        policy_decisions = []

        # Check policy for ListBuckets
        print("📜 Checking policy for s3:ListBuckets...")
        list_decision = self._check_policy("s3:ListBuckets")
        if not list_decision.allowed:
            print(f"❌ Policy denies s3:ListBuckets: {list_decision.reason}")
            return {"deleted": [], "errors": [{"error": list_decision.reason}]}

        # List all demo buckets
        response = self.s3.list_buckets()
        demo_buckets = [b["Name"] for b in response["Buckets"] if fnmatch.fnmatch(b["Name"], "aimgentix-demo-*")]

        print(f"Found {len(demo_buckets)} demo buckets to clean up")
        print("")

        for bucket_name in demo_buckets:
            try:
                print(f"🗑️  Cleaning up bucket: {bucket_name}")

                # Delete all objects first - CHECK POLICY FOR EACH
                objects = self.s3.list_objects_v2(Bucket=bucket_name)
                if "Contents" in objects:
                    for obj in objects["Contents"]:
                        print("   📜 Checking policy for s3:DeleteObject...")
                        try:
                            self._require_policy("s3:DeleteObject", bucket_name=bucket_name, key=obj["Key"])
                            policy_decisions.append({"action": "s3:DeleteObject", "allowed": True})

                            self.s3.delete_object(Bucket=bucket_name, Key=obj["Key"])
                            print(f"   ✅ Deleted object: {obj['Key']}")

                            self._emit_event(
                                ActionType.API_CALL,
                                f"s3:DeleteObject:{bucket_name}/{obj['Key']}",
                                EventStatus.SUCCESS,
                                metadata={"bucket_name": bucket_name, "key": obj["Key"]},
                            )
                        except PolicyViolation as pv:
                            policy_decisions.append(
                                {"action": "s3:DeleteObject", "allowed": False, "reason": pv.decision.reason}
                            )
                            errors.append(
                                {
                                    "bucket": bucket_name,
                                    "key": obj["Key"],
                                    "error": f"Policy violation: {pv.decision.reason}",
                                }
                            )
                            print(f"   ❌ Policy violation: {pv.decision.reason}")
                            continue

                # Delete bucket - CHECK POLICY FIRST
                print("   📜 Checking policy for s3:DeleteBucket...")
                self._require_policy("s3:DeleteBucket", bucket_name=bucket_name)
                policy_decisions.append({"action": "s3:DeleteBucket", "allowed": True})

                self.s3.delete_bucket(Bucket=bucket_name)
                deleted.append(bucket_name)
                print(f"   ✅ Deleted bucket: {bucket_name}")

                self._emit_event(
                    ActionType.API_CALL,
                    f"s3:DeleteBucket:{bucket_name}",
                    EventStatus.SUCCESS,
                    metadata={"bucket_name": bucket_name},
                )

            except PolicyViolation as pv:
                policy_decisions.append({"action": "s3:DeleteBucket", "allowed": False, "reason": pv.decision.reason})
                errors.append({"bucket": bucket_name, "error": f"Policy violation: {pv.decision.reason}"})
                print(f"   ❌ Policy violation: {pv.decision.reason}")

            except Exception as e:
                errors.append({"bucket": bucket_name, "error": str(e)})
                print(f"   ❌ Error deleting {bucket_name}: {e}")

        self.audit.flush()
        self.audit.close()

        print("")
        print(f"✅ Cleanup complete. Deleted {len(deleted)} buckets, {len(errors)} errors.")
        return {"deleted": deleted, "errors": errors, "policy_decisions": policy_decisions}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    agent = S3LifecycleAgent()

    if command == "investigate":
        agent.investigate()
    elif command == "act":
        agent.act()
    elif command == "cleanup":
        agent.cleanup()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
