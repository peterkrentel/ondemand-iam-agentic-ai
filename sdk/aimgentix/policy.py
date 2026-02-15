"""
Policy enforcement for AIMgentix SDK.

Implements the policy evaluation order from specs/gha-agent-runtime.md:
  1. Check denied_actions - if match, DENY
  2. Check rate_limits - if exceeded, DENY
  3. Check allowed_actions - if no match, DENY
  4. Check requires_approval - if true, require gate
  5. Otherwise, ALLOW
"""

import fnmatch
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class PolicyDecision:
    """Result of a policy check."""

    allowed: bool
    reason: str
    requires_approval: bool = False
    matched_rule: Optional[Dict[str, Any]] = None


class PolicyViolation(Exception):
    """Raised when an action violates policy."""

    def __init__(self, decision: PolicyDecision):
        self.decision = decision
        super().__init__(decision.reason)


class PolicyEnforcer:
    """
    Enforces AIMgentix agent policies.

    Follows the evaluation order from specs/gha-agent-runtime.md:
      1. Check denied_actions - if match, DENY
      2. Check rate_limits - if exceeded, DENY
      3. Check allowed_actions - if no match, DENY
      4. Check requires_approval - if true, require gate
      5. Otherwise, ALLOW
    """

    def __init__(self, policy_path: Path):
        """Load policy from YAML file."""
        if not policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {policy_path}")

        with open(policy_path) as f:
            self.policy = yaml.safe_load(f)

        self.name = self.policy.get("name", "unknown")
        self.version = self.policy.get("version", 1)
        self.allowed_actions = self.policy.get("allowed_actions", [])
        self.denied_actions = self.policy.get("denied_actions", [])
        self.rate_limits = self.policy.get("rate_limits", [])
        self.auto_approve = self.policy.get("auto_approve", [])

        # Track rate limit usage (in-memory for now, v2 will use external store)
        self._rate_counts: Dict[str, int] = {}

    def check(self, action_type: str, **context: Any) -> PolicyDecision:
        """
        Check if an action is allowed by policy.

        Args:
            action_type: The action type (e.g., "s3:CreateBucket")
            **context: Additional context (bucket_name, region, etc.)

        Returns:
            PolicyDecision with allowed/denied status and reason
        """
        # Step 1: Check denied_actions - if match, DENY
        for rule in self.denied_actions:
            if self._matches_rule(action_type, rule, context):
                return PolicyDecision(
                    allowed=False,
                    reason=f"Action denied by policy rule: {rule.get('type')}",
                    matched_rule=rule,
                )

        # Step 2: Check rate_limits - if exceeded, DENY
        for limit in self.rate_limits:
            if self._matches_action_pattern(action_type, limit.get("action", "")):
                max_per_hour = limit.get("max_per_hour", 999999)
                current_count = self._rate_counts.get(action_type, 0)
                if current_count >= max_per_hour:
                    return PolicyDecision(
                        allowed=False,
                        reason=f"Rate limit exceeded: {action_type} ({current_count}/{max_per_hour} per hour)",
                        matched_rule=limit,
                    )

        # Step 3: Check allowed_actions - if no match, DENY
        matched_allow_rule = None
        for rule in self.allowed_actions:
            if self._matches_rule(action_type, rule, context):
                matched_allow_rule = rule
                break

        if not matched_allow_rule:
            return PolicyDecision(
                allowed=False,
                reason=f"Action not in allowed_actions: {action_type}",
                matched_rule=None,
            )

        # Step 4: Check requires_approval
        requires_approval = matched_allow_rule.get("requires_approval", False)

        # Step 5: ALLOW - Increment rate limit counter
        self._rate_counts[action_type] = self._rate_counts.get(action_type, 0) + 1

        return PolicyDecision(
            allowed=True,
            reason=f"Allowed by policy rule: {matched_allow_rule.get('type')}",
            requires_approval=requires_approval,
            matched_rule=matched_allow_rule,
        )

    def check_batch(self, actions: List[Dict[str, Any]]) -> PolicyDecision:
        """
        Check multiple actions as a batch (per spec v1.1).

        Per spec: If ANY action is denied, entire batch is DENIED.
        If ANY action requires approval, entire batch requires approval.
        """
        requires_approval = False
        for action in actions:
            action_type = action.get("type", "")
            context = {k: v for k, v in action.items() if k != "type"}
            decision = self.check(action_type, **context)
            if not decision.allowed:
                return decision
            if decision.requires_approval:
                requires_approval = True

        return PolicyDecision(
            allowed=True,
            reason=f"Batch of {len(actions)} actions allowed",
            requires_approval=requires_approval,
        )

    def _matches_rule(self, action_type: str, rule: Dict, context: Dict) -> bool:
        """Check if an action matches a policy rule."""
        rule_type = rule.get("type", "")

        # Check action type pattern
        if not self._matches_action_pattern(action_type, rule_type):
            return False

        # Check conditions
        conditions = rule.get("conditions", {})
        return self._check_conditions(conditions, context)

    def _check_conditions(self, conditions: Dict, context: Dict) -> bool:
        """Check if context matches all conditions."""
        for key, expected in conditions.items():
            actual = context.get(key)

            if key == "bucket_name_pattern":
                # Glob pattern match for bucket names
                bucket_name = context.get("bucket_name", "")
                if not fnmatch.fnmatch(bucket_name, expected):
                    return False
            elif key == "region":
                # Region must be in allowed list
                if isinstance(expected, list):
                    if actual not in expected:
                        return False
                elif actual != expected:
                    return False
            else:
                # Exact match for other conditions
                if actual != expected:
                    return False

        return True

    def _matches_action_pattern(self, action: str, pattern: str) -> bool:
        """Check if action matches pattern (supports wildcards)."""
        if pattern == "*" or pattern == action:
            return True

        # Handle s3:* style wildcards
        if pattern.endswith(":*"):
            prefix = pattern[:-1]  # "s3:"
            return action.startswith(prefix)

        return fnmatch.fnmatch(action, pattern)

    def get_auto_approve_actions(self, risk_level: str) -> List[str]:
        """Get list of actions that can be auto-approved for a risk level."""
        for rule in self.auto_approve:
            if rule.get("risk_level") == risk_level:
                return rule.get("actions", [])
        return []

    def can_auto_approve(self, action_type: str, risk_level: str) -> bool:
        """Check if an action can be auto-approved for a given risk level."""
        auto_approve_actions = self.get_auto_approve_actions(risk_level)
        return action_type in auto_approve_actions

    def reset_rate_limits(self) -> None:
        """Reset rate limit counters (called hourly in production)."""
        self._rate_counts = {}

