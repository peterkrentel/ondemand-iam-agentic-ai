# GitHub Actions Agent Runtime Spec (v1)

**Status**: Active
**Last Updated**: 2026-02-01
**Applies To**: GitHub Actions workflows, agent execution, permission boundaries
**Why This Exists**: Defines the contract for running agents as ephemeral GitHub Actions jobs with permission gates
**Validation**: Workflow schema validation, contract tests, audit trail verification

---

## Overview

This spec defines how to run AI agents as GitHub Actions workflows with explicit permission boundaries, approval gates, and complete audit trails.

**Core Principle**: GitHub Actions is the control plane. Agents run as ephemeral compute with job-level permissions.

---

## Architecture

```
Alert / Manual Trigger
↓
Investigate Job (read-only)
├── Agent analyzes situation
├── Outputs recommendation
└── Creates audit trail
↓
Approval Gate (environment protection)
├── Human review (manual)
└── Policy evaluation (automated)
↓
Act Job (elevated permissions)
├── Agent executes action
└── Creates audit trail
↓
Artifacts + Complete Logs
```

---

## Workflow Contract

### Required Jobs

All agent workflows MUST include these three jobs in order:

1. **investigate** - Read-only analysis
2. **approve** - Human or automated approval gate
3. **act** - Execute action with elevated permissions

### Job Permissions

#### Investigate Job MUST:
- Have `contents: read` permission ONLY
- NOT have write permissions
- NOT have secrets access (except audit API)
- Output findings as job outputs
- Create audit events via AIMgentix SDK

#### Approve Job MUST:
- Use GitHub environment with protection rules
- Depend on `investigate` job (`needs: investigate`)
- NOT execute any code (approval only)
- Support both manual and automated approval

#### Act Job MUST:
- Depend on `approve` job (`needs: approve`)
- Have minimum required permissions for action
- Create audit events via AIMgentix SDK
- Be idempotent (safe to retry)

---

## Workflow Inputs

Workflows MUST accept these inputs:

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `trigger_source` | string | YES | Source of trigger: `manual`, `alert`, `schedule` |
| `trace_id` | string | YES | Unique trace ID for correlating all events |
| `resource` | string | YES | Target resource for investigation/action |
| `action_context` | string | NO | Additional context (JSON string) |

---

## Workflow Outputs

Workflows MUST produce these artifacts:

| Artifact | Type | Required | Description |
|----------|------|----------|-------------|
| `investigation-report.json` | JSON | YES | Investigation findings and recommendations |
| `audit-trace-id.txt` | Text | YES | Trace ID for AIMgentix audit lookup |
| `action-result.json` | JSON | NO | Result of action execution (if act job runs) |

---

## Audit Trail Requirements

### All jobs MUST:
- Use AIMgentix SDK to capture events
- Include `trace_id` in all audit events
- Set `agent_instance_id` to workflow run ID
- Capture start, end, and error events

### Event Types Required:

**Investigate Job**:
- `action_type: tool_call` for each investigation step
- `status: success/error` for outcome

**Act Job**:
- `action_type: api_call` (or specific type) for action
- `status: success/error` for outcome
- `latency_ms` for action duration

---

## Permission Boundary Rules

### MUST NOT:
- Grant write permissions to investigate job
- Skip approval gate for production actions
- Share credentials between investigate and act jobs
- Use personal access tokens (use GITHUB_TOKEN)

### MUST:
- Use job-level permissions (not workflow-level)
- Use environment secrets for act job only
- Implement timeout limits on all jobs
- Log all permission grants to audit trail

---

## Approval Gate Types

### Manual Approval:
- Uses GitHub environment protection rules
- Requires 1+ human reviewer
- Shows investigation findings in environment

### Automated Approval:
- Evaluates investigation output against policy
- Logs approval decision to audit trail
- Falls back to manual if policy uncertain

---

## Example Workflow Structure

```yaml
name: Agent Workflow - Investigate & Act

on:
  workflow_dispatch:
    inputs:
      trigger_source:
        required: true
        type: string
      trace_id:
        required: true
        type: string
      resource:
        required: true
        type: string

jobs:
  investigate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    outputs:
      recommendation: ${{ steps.analyze.outputs.recommendation }}
      safe_to_proceed: ${{ steps.analyze.outputs.safe_to_proceed }}
    steps:
      - uses: actions/checkout@v4
      - name: Investigate
        id: analyze
        run: python agent.py investigate
      - name: Save Investigation Report
        run: |
          echo "$FINDINGS" > investigation-report.json
      - uses: actions/upload-artifact@v4
        with:
          name: investigation-report
          path: investigation-report.json

  approve:
    needs: investigate
    environment: production-approval
    runs-on: ubuntu-latest
    steps:
      - name: Show Investigation Results
        run: |
          echo "Recommendation: ${{ needs.investigate.outputs.recommendation }}"
          echo "Safe to proceed: ${{ needs.investigate.outputs.safe_to_proceed }}"

  act:
    needs: approve
    runs-on: ubuntu-latest
    permissions:
      deployments: write
    steps:
      - uses: actions/checkout@v4
      - name: Execute Action
        run: python agent.py act --resource "${{ inputs.resource }}"
      - uses: actions/upload-artifact@v4
        with:
          name: action-result
          path: action-result.json
```

---

## Validation

### Schema Validation:
- Workflow inputs match spec
- Required jobs exist in order
- Permissions are correctly scoped

### Contract Tests:
- Investigate job produces required outputs
- Act job depends on approve job
- Audit events are created

### Runtime Validation:
- GitHub Actions enforces environment protection
- Job permissions are enforced by GitHub
- Audit trail is complete

---

## Compatibility Rules

### ✅ ALLOWED (non-breaking):
- Adding new optional inputs
- Adding new workflow outputs
- Adding new audit event types
- Adding new approval methods

### ❌ NOT ALLOWED (breaking):
- Removing required inputs
- Changing job execution order
- Removing permission boundaries
- Skipping audit trail

---

## Security Requirements

### MUST:
- Use ephemeral runners (no self-hosted without justification)
- Rotate credentials between jobs
- Validate all inputs
- Rate limit workflow triggers

### MUST NOT:
- Store secrets in logs
- Expose credentials in artifacts
- Skip security scanning
- Allow workflow_run triggers without validation

---

## Acceptance Criteria

### AC-1: ✅ Valid Minimal Workflow
- Has investigate, approve, act jobs in order
- Investigate has read-only permissions
- Approve uses environment protection
- Act has scoped write permissions
- Creates audit trail

### AC-2: ✅ Manual Trigger
- Accepts required inputs
- Creates trace_id artifact
- Waits for human approval
- Executes action after approval

### AC-3: ✅ Audit Trail Complete
- All jobs create AIMgentix events
- Same trace_id across all events
- Events captured before and after each step
- Success/error status recorded

### AC-4: ❌ Invalid - Skipped Approval
- Act job runs without approve job
- Expected: Workflow validation fails

### AC-5: ❌ Invalid - Wrong Permissions
- Investigate job has write permissions
- Expected: Spec violation (manual check)

---

## References

- **Workflow Implementation**: `.github/workflows/agent-investigate-act.yml`
- **Spec Policy**: `specs/SPEC_POLICY.md`
- **AIMgentix Integration**: `sdk/aimgentix/`
- **Documentation**: `docs/GITHUB_ACTIONS_RUNTIME.md`

---

**This spec defines public contracts. Changes require following the compatibility rules above.**
