# GitHub Actions Agent Runtime Spec (v1)

**Status**: Active
**Last Updated**: 2026-02-01
**Applies To**: Agent workflows, SDK integration, policy enforcement
**Why This Exists**: Agents need ephemeral compute, scoped permissions, and audit trails. GitHub Actions provides all three.
**Validation**: `.github/workflows/` structure, `tests/test_workflow_contracts.py`

---

## Core Concept

GitHub Actions IS the agent runtime. Agents run as workflows with:
- **Ephemeral compute** (runners spin up, execute, die)
- **Scoped permissions** (per-job `permissions:` blocks)
- **Approval gates** (environment protection rules)
- **Audit trail** (workflow logs, artifacts, git history)

---

## Prerequisites: AWS OIDC Bootstrap

Before agents can access AWS resources, you MUST bootstrap OIDC federation. This is a **one-time local operation** that enables all subsequent agent runs to use short-lived, scoped credentials.

### Why OIDC?

| Approach | Security | Rotation | Scope |
|----------|----------|----------|-------|
| ❌ Hardcoded keys | Critical risk | Manual | Often over-permissioned |
| ❌ GitHub Secrets (static keys) | Medium risk | Manual | Can be scoped |
| ✅ **OIDC Federation** | Low risk | Automatic (per-run) | Per-repo, per-workflow |

### Bootstrap Process

**Run once from your laptop** (requires `aws configure` with IAM permissions):

```bash
cd infra
./deploy-oidc.sh <github-org> <github-repo>
```

This deploys a CloudFormation stack (`infra/github-oidc.cfn.yaml`) that creates:
1. **OIDC Identity Provider** - Allows GitHub to authenticate to AWS
2. **IAM Role** - Scoped to your specific repo, assumable only via OIDC
3. **Permissions Policy** - Scoped to allowed resources (e.g., `aimgentix-demo-*` buckets)

### Post-Bootstrap Configuration

After running the bootstrap script:

1. **Add the Role ARN to GitHub Secrets**:
   - Settings → Secrets and variables → Actions → New repository secret
   - Name: `AWS_ROLE_ARN`
   - Value: (output from bootstrap script)

2. **Create GitHub Environments** (for approval gates):
   - Settings → Environments → New environment
   - `agent-approval` - Add required reviewers
   - `production` - Optional additional protection

3. **Verify** by running an agent workflow:
   ```bash
   gh workflow run s3-lifecycle-agent.yml
   ```

### How Workflows Use OIDC

```yaml
jobs:
  investigate:
    permissions:
      id-token: write   # Required for OIDC
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
```

The `id-token: write` permission allows the workflow to request a GitHub OIDC token, which AWS exchanges for short-lived credentials (1 hour max).

### Teardown

To remove all AWS resources:
```bash
aws cloudformation delete-stack --stack-name aimgentix-github-oidc
```

---

## The Three-Phase Pattern

All agent workflows MUST follow the **Investigate → Approve → Act** pattern:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   INVESTIGATE   │────▶│     APPROVE     │────▶│      ACT        │
│   (read-only)   │     │  (gate/review)  │     │   (elevated)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Phase 1: INVESTIGATE

**Purpose**: Gather information, analyze situation, propose action

**Permissions**: MUST be read-only
```yaml
permissions:
  contents: read
  # NO write permissions
```

**Requirements**:
- MUST NOT modify any resources
- MUST output findings as workflow artifact
- MUST output proposed action as job output
- MUST log all operations via AIMgentix SDK

**Outputs**:
- `findings.json` - What the agent discovered
- `proposed_action` - What the agent wants to do
- `risk_level` - `low`, `medium`, `high`, `critical`

### Phase 2: APPROVE

**Purpose**: Gate between investigation and action

**Permissions**: None required (gate only)

**Requirements**:
- MUST use GitHub environment with protection rules
- MUST block if `risk_level` is `high` or `critical` (require human review)
- MAY auto-approve if `risk_level` is `low` and policy allows
- MUST log approval decision via AIMgentix SDK

**Auto-Approve Rules**:
- `risk_level: low` + action in allowlist → auto-approve
- `risk_level: medium` + action in allowlist + within rate limit → auto-approve
- All other cases → require human review

### Phase 3: ACT

**Purpose**: Execute the approved action

**Permissions**: Scoped to specific action
```yaml
permissions:
  contents: write  # Only if needed
  # Minimum required for the action
```

**Requirements**:
- MUST only execute the approved action (no deviation)
- MUST use scoped credentials (not admin tokens)
- MUST log all operations via AIMgentix SDK
- MUST output results as workflow artifact

---

## Permission Scoping Rules

### MUST: Principle of Least Privilege

Each job MUST request only the permissions it needs:

```yaml
# ❌ BAD: Over-permissioned
permissions: write-all

# ✅ GOOD: Scoped to need
permissions:
  contents: read
  issues: write
```

### MUST: No Permission Escalation Without Gate

A job with elevated permissions MUST:
1. Depend on an approval gate (`needs: approve`)
2. Use a protected environment (`environment: production`)

```yaml
# ❌ BAD: Elevated permissions without gate
act:
  permissions:
    contents: write
  steps:
    - run: ./dangerous-action.sh

# ✅ GOOD: Elevated permissions with gate
act:
  needs: approve
  environment: production
  permissions:
    contents: write
  steps:
    - run: ./dangerous-action.sh
```

### MUST: Explicit Permission Declaration

All agent workflows MUST declare permissions explicitly:

```yaml
# ❌ BAD: Implicit permissions (inherits repo defaults)
jobs:
  investigate:
    steps: ...

# ✅ GOOD: Explicit permissions
jobs:
  investigate:
    permissions:
      contents: read
    steps: ...
```

---

## AIMgentix SDK Integration

### Environment Variables

The SDK MUST read these from GitHub Actions environment:

| Variable | Source | Purpose |
|----------|--------|---------|
| `AIMGENTIX_TRACE_ID` | `${{ github.run_id }}-${{ github.run_attempt }}` | Correlate events |
| `AIMGENTIX_AGENT_ID` | `${{ github.workflow }}-${{ github.job }}` | Identify agent |
| `AIMGENTIX_ACTOR` | `system` | Actor type for GHA runs |
| `GITHUB_REPOSITORY` | Built-in | Context |
| `GITHUB_SHA` | Built-in | Context |
| `GITHUB_REF` | Built-in | Context |

### Required Events

Each phase MUST emit these events:

**INVESTIGATE phase**:
- `action_type: api_call` for each external API call
- `action_type: file_read` for each file read
- Final event with `metadata.phase: investigate`, `metadata.findings: <summary>`

**APPROVE phase**:
- `action_type: api_call` with `resource: approval_gate`
- `metadata.decision: approved|denied|pending`
- `metadata.approver: auto|<github_username>`

**ACT phase**:
- `action_type: <appropriate>` for each action taken
- Final event with `metadata.phase: act`, `metadata.result: <summary>`

---

## Artifact Requirements

### MUST: Structured Outputs

Each phase MUST output structured JSON artifacts:

**investigate/findings.json**:
```json
{
  "timestamp": "2026-02-01T10:00:00Z",
  "trace_id": "12345-1",
  "findings": [...],
  "proposed_action": {
    "type": "create_bucket",
    "parameters": {...}
  },
  "risk_level": "low"
}
```

**act/results.json**:
```json
{
  "timestamp": "2026-02-01T10:05:00Z",
  "trace_id": "12345-1",
  "action_taken": "create_bucket",
  "success": true,
  "details": {...}
}
```

### MUST: Artifact Retention

- Artifacts MUST be retained for at least 90 days
- Artifacts MUST be uploaded even on failure

---

## Policy Definition

Policies define what agents can do. Policies are YAML files in `.github/agent-policies/`.

### Policy Schema

```yaml
# .github/agent-policies/s3-lifecycle.yaml
name: s3-lifecycle-agent
version: 1

# What actions are allowed
allowed_actions:
  - type: s3:CreateBucket
    conditions:
      region: [us-east-1, us-west-2]
  - type: s3:PutLifecycleConfiguration
  - type: s3:PutObject
  - type: s3:DeleteBucket
    requires_approval: true

# What actions are denied (overrides allowed)
denied_actions:
  - type: s3:*
    conditions:
      bucket_name_pattern: "prod-*"

# Rate limits
rate_limits:
  - action: s3:CreateBucket
    max_per_hour: 5

# Auto-approve rules
auto_approve:
  - risk_level: low
    actions: [s3:CreateBucket, s3:PutObject]
  - risk_level: medium
    actions: [s3:PutLifecycleConfiguration]
```

### Policy Evaluation Order

1. Check `denied_actions` - if match, DENY
2. Check `rate_limits` - if exceeded, DENY
3. Check `allowed_actions` - if no match, DENY
4. Check `requires_approval` - if true, require gate
5. Otherwise, ALLOW

---

## Approval Gate Semantics

### Environment Protection Rules

Approval gates use GitHub environment protection:

```yaml
# In workflow
approve:
  environment: agent-approval  # Must be configured in repo settings
  needs: investigate
```

**Environment Configuration** (in GitHub repo settings):

- Required reviewers: 1+ for `high`/`critical` risk
- Wait timer: Optional delay before auto-approve
- Deployment branches: Restrict which branches can trigger

### Auto-Approve Logic

```text
IF risk_level == "low" AND action in policy.auto_approve:
  → Auto-approve (no human needed)
ELIF risk_level == "medium" AND action in policy.auto_approve AND within_rate_limit:
  → Auto-approve with logging
ELIF risk_level == "high" OR risk_level == "critical":
  → Require human review (environment protection)
ELSE:
  → Require human review
```

### Approval Timeout

- If no approval within 24 hours, workflow MUST fail
- Timeout is configurable per environment

---

## Validation

### Workflow Structure Validation

CI MUST validate that agent workflows follow the pattern:

```yaml
# .github/workflows/validate-agent-workflows.yml
- name: Validate agent workflow structure
  run: |
    # Check for three-phase pattern
    # Check for explicit permissions
    # Check for environment gates
    # Check for artifact uploads
```

### Contract Tests

`tests/test_workflow_contracts.py` MUST validate:

- All agent workflows have investigate → approve → act structure
- No job has `permissions: write-all`
- ACT jobs depend on APPROVE jobs
- ACT jobs use protected environments
- All phases upload artifacts

### Policy Validation

CI MUST validate policy files:

- Valid YAML syntax
- Schema compliance
- No conflicting rules (allow + deny same action)

---

## Acceptance Criteria

### WF-1: ✅ Valid Agent Workflow (Minimal)

```yaml
name: S3 Lifecycle Agent
on: workflow_dispatch

jobs:
  investigate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    outputs:
      risk_level: ${{ steps.analyze.outputs.risk_level }}
    steps:
      - uses: actions/checkout@v4
      - run: python agent.py investigate
        id: analyze
      - uses: actions/upload-artifact@v4
        with:
          name: findings
          path: findings.json

  approve:
    needs: investigate
    runs-on: ubuntu-latest
    environment: agent-approval
    steps:
      - run: echo "Approved"

  act:
    needs: approve
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # For AWS OIDC
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: python agent.py act
      - uses: actions/upload-artifact@v4
        with:
          name: results
          path: results.json
```

### WF-2: ❌ Invalid Workflow (No Gate)

```yaml
jobs:
  act:
    # ❌ No 'needs: approve'
    # ❌ No 'environment:'
    permissions:
      contents: write
    steps:
      - run: ./dangerous-action.sh
```

**Expected**: CI fails with "ACT job must depend on APPROVE job"

### WF-3: ❌ Invalid Workflow (Over-Permissioned)

```yaml
jobs:
  investigate:
    permissions: write-all  # ❌ Too broad
    steps:
      - run: python agent.py investigate
```

**Expected**: CI fails with "INVESTIGATE job must have read-only permissions"

### WF-4: ❌ Invalid Workflow (No Artifacts)

```yaml
jobs:
  investigate:
    permissions:
      contents: read
    steps:
      - run: python agent.py investigate
      # ❌ No artifact upload
```

**Expected**: CI fails with "INVESTIGATE job must upload findings artifact"

---

## References

- **Implementation**: `.github/workflows/` (agent workflows)
- **Policies**: `.github/agent-policies/` (policy definitions)
- **SDK**: `sdk/aimgentix/gha.py` (GitHub Actions integration)
- **Contract Tests**: `tests/test_workflow_contracts.py`
- **Event Schema**: `specs/event-schema.md`
