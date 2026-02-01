# GitHub Actions Agent Contracts (v1)

**Status**: Active
**Last Updated**: 2026-02-01
**Applies To**: Agent code ↔ Workflow YAML ↔ Policy definitions ↔ SDK
**Why This Exists**: Multiple components must agree on data formats and interfaces.
**Validation**: `tests/test_workflow_contracts.py`, `tests/test_policy_contracts.py`

---

## Contract 1: Agent Code ↔ Workflow YAML

### Job Outputs Contract

The agent code MUST produce outputs that the workflow can consume:

**INVESTIGATE job outputs**:

```python
# Agent code MUST write to $GITHUB_OUTPUT
with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(f"risk_level={risk_level}\n")
    f.write(f"proposed_action={json.dumps(action)}\n")
    f.write(f"findings_summary={summary}\n")
```

**Workflow MUST declare outputs**:

```yaml
investigate:
  outputs:
    risk_level: ${{ steps.analyze.outputs.risk_level }}
    proposed_action: ${{ steps.analyze.outputs.proposed_action }}
    findings_summary: ${{ steps.analyze.outputs.findings_summary }}
```

### Output Schema

| Output | Type | Required | Values |
|--------|------|----------|--------|
| `risk_level` | string | YES | `low`, `medium`, `high`, `critical` |
| `proposed_action` | JSON string | YES | Action object (see below) |
| `findings_summary` | string | YES | Human-readable summary |

**Proposed Action Schema**:

```json
{
  "type": "string",           // Action type (e.g., "s3:CreateBucket")
  "parameters": {},           // Action-specific parameters
  "reason": "string",         // Why this action is proposed
  "reversible": true          // Can this action be undone?
}
```

---

## Contract 2: Investigation → Approval → Action Data Flow

### Artifact Contract

Each phase produces artifacts that subsequent phases MAY consume:

**findings.json** (INVESTIGATE → APPROVE):

```json
{
  "schema_version": "1.0",
  "timestamp": "2026-02-01T10:00:00Z",
  "trace_id": "12345-1",
  "agent_id": "s3-lifecycle-agent",
  "findings": [
    {
      "type": "observation",
      "message": "No existing bucket found",
      "severity": "info"
    }
  ],
  "proposed_action": {
    "type": "s3:CreateBucket",
    "parameters": {
      "bucket_name": "test-lifecycle-bucket-abc123",
      "region": "us-east-1"
    },
    "reason": "Need bucket for lifecycle demo",
    "reversible": true
  },
  "risk_assessment": {
    "level": "low",
    "factors": ["new resource", "non-production", "reversible"]
  }
}
```

**results.json** (ACT → Audit):

```json
{
  "schema_version": "1.0",
  "timestamp": "2026-02-01T10:05:00Z",
  "trace_id": "12345-1",
  "agent_id": "s3-lifecycle-agent",
  "action_taken": {
    "type": "s3:CreateBucket",
    "parameters": {
      "bucket_name": "test-lifecycle-bucket-abc123",
      "region": "us-east-1"
    }
  },
  "success": true,
  "details": {
    "bucket_arn": "arn:aws:s3:::test-lifecycle-bucket-abc123",
    "creation_time": "2026-02-01T10:05:00Z"
  },
  "audit_events": ["event-id-1", "event-id-2"]
}
```

---

## Contract 3: Policy Definition ↔ GitHub Permissions

### Mapping Rules

Policy `allowed_actions` MUST map to GitHub `permissions:`:

| Policy Action Type | GitHub Permission | Scope |
|--------------------|-------------------|-------|
| `s3:*` | `id-token: write` | AWS OIDC |
| `github:contents:read` | `contents: read` | Repo |
| `github:contents:write` | `contents: write` | Repo |
| `github:issues:write` | `issues: write` | Issues |
| `github:deployments:write` | `deployments: write` | Deployments |

### Policy File Location

Policies MUST be in `.github/agent-policies/<agent-name>.yaml`

### Policy Schema

```yaml
# Required fields
name: string                    # Agent name (must match workflow)
version: integer                # Policy version

# Optional fields
allowed_actions:                # List of allowed actions
  - type: string                # Action type pattern
    conditions: object          # Optional conditions
    requires_approval: boolean  # Default: false

denied_actions:                 # List of denied actions (overrides allowed)
  - type: string
    conditions: object

rate_limits:                    # Rate limiting rules
  - action: string
    max_per_hour: integer

auto_approve:                   # Auto-approval rules
  - risk_level: string          # low, medium
    actions: [string]           # Action types to auto-approve
```

---

## Contract 4: SDK ↔ GitHub Actions Environment

### Required Environment Variables

The SDK MUST read these variables when running in GitHub Actions:

| Variable | Required | Source | Example |
|----------|----------|--------|---------|
| `GITHUB_ACTIONS` | YES | Built-in | `true` |
| `GITHUB_RUN_ID` | YES | Built-in | `12345` |
| `GITHUB_RUN_ATTEMPT` | YES | Built-in | `1` |
| `GITHUB_WORKFLOW` | YES | Built-in | `s3-lifecycle-agent` |
| `GITHUB_JOB` | YES | Built-in | `investigate` |
| `GITHUB_REPOSITORY` | YES | Built-in | `owner/repo` |
| `GITHUB_SHA` | YES | Built-in | `abc123...` |
| `GITHUB_REF` | YES | Built-in | `refs/heads/main` |
| `GITHUB_OUTPUT` | YES | Built-in | Path to output file |
| `AIMGENTIX_API_URL` | NO | Secret/Var | `https://api.aimgentix.io` |
| `AIMGENTIX_API_KEY` | NO | Secret | API key for remote logging |

### SDK Initialization in GHA

```python
from aimgentix import AuditClient
from aimgentix.gha import GitHubActionsContext

# Auto-detect GitHub Actions environment
ctx = GitHubActionsContext.from_environment()

client = AuditClient(
    api_url=os.getenv('AIMGENTIX_API_URL', 'http://localhost:8000'),
    trace_id=ctx.trace_id,      # {run_id}-{run_attempt}
    agent_id=ctx.agent_id,      # {workflow}-{job}
)
```

### Event Metadata in GHA

All events emitted in GitHub Actions MUST include:

```json
{
  "metadata": {
    "gha": {
      "run_id": "12345",
      "run_attempt": "1",
      "workflow": "s3-lifecycle-agent",
      "job": "investigate",
      "repository": "owner/repo",
      "sha": "abc123...",
      "ref": "refs/heads/main"
    }
  }
}
```

---

## Validation

### Contract Tests

`tests/test_workflow_contracts.py` validates:

- Job outputs match expected schema
- Artifact JSON matches expected schema
- Policy files are valid YAML with required fields
- SDK correctly reads GHA environment variables

### Schema Validation

All JSON artifacts MUST include `schema_version` field for forward compatibility.

### CI Enforcement

`.github/workflows/validate-contracts.yml` runs on every PR:

1. Parse all workflow files in `.github/workflows/`
2. Validate agent workflows follow three-phase pattern
3. Validate policy files match schema
4. Run contract tests

---

## Acceptance Criteria

### CT-1: ✅ Valid Job Output

```python
# Agent writes valid output
with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write("risk_level=low\n")
    f.write('proposed_action={"type":"s3:CreateBucket"}\n')
```

**Expected**: Workflow can read `${{ steps.analyze.outputs.risk_level }}`

### CT-2: ❌ Invalid Risk Level

```python
f.write("risk_level=unknown\n")  # ❌ Not in allowed values
```

**Expected**: Approval job fails validation

### CT-3: ✅ Valid Policy File

```yaml
name: my-agent
version: 1
allowed_actions:
  - type: s3:GetObject
```

**Expected**: Policy validation passes

### CT-4: ❌ Invalid Policy File

```yaml
# Missing required 'name' field
version: 1
allowed_actions:
  - type: s3:GetObject
```

**Expected**: CI fails with "Policy missing required field: name"

---

## References

- **Runtime Spec**: `specs/gha-agent-runtime.md`
- **Event Schema**: `specs/event-schema.md`
- **Contract Tests**: `tests/test_workflow_contracts.py`
- **Policy Tests**: `tests/test_policy_contracts.py`
