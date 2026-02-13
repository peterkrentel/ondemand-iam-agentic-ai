# 🚀 GitHub Actions as Agent Runtime

**Last Updated**: 2026-02-01

---

## 🎯 Overview

This document describes how to use **GitHub Actions as the agent runtime** - an automation-first, CI/CD-native approach to running AI agents with built-in permission gates, audit trails, and approval workflows.

**Key Insight**: GitHub Actions provides everything agents need without custom infrastructure:
- ✅ Ephemeral compute (runners)
- ✅ Strong identity & permissions
- ✅ Native approval gates
- ✅ Complete audit logs
- ✅ Zero infrastructure to manage

---

## 🧠 Mental Model

Think in **planes**, not environments:

| Plane | Implementation |
|-------|----------------|
| **Control Plane** | GitHub (workflows, approvals, runs) |
| **Execution Plane** | Ephemeral runners (no persistent state) |
| **Policy Plane** | Versioned workflow files + environment protection |
| **Audit Plane** | Git history + AIMgentix events + workflow logs |

This eliminates:
- ❌ Local development snowflakes
- ❌ "Pet" environments
- ❌ Implicit permissions
- ❌ Hidden state

---

## 📊 The Pattern: Investigate → Approve → Act

### Flow Diagram

```
Alert / Manual Trigger
↓
┌─────────────────────────┐
│  INVESTIGATE (read-only)│
│  ─────────────────────  │
│  • Analyze situation    │
│  • Gather evidence      │
│  • Output recommendation│
│  • Create audit events  │
└─────────────────────────┘
↓
┌─────────────────────────┐
│  APPROVE (gate)         │
│  ──────────────────     │
│  • Human review OR      │
│  • Policy evaluation    │
│  • Environment protection│
└─────────────────────────┘
↓
┌─────────────────────────┐
│  ACT (elevated perms)   │
│  ─────────────────────  │
│  • Execute approved action│
│  • Minimal permissions  │
│  • Create audit events  │
└─────────────────────────┘
↓
Complete Audit Trail
```

---

## 🛠️ Implementation

### Workflow File

See: `.github/workflows/agent-investigate-act.yml`

**Key Features**:
1. **Job-level permissions** - Each job has minimal required permissions
2. **Environment protection** - Approval gate enforced by GitHub
3. **Audit integration** - All actions logged to AIMgentix
4. **Artifacts** - Investigation reports, action results, trace IDs

### Permission Boundaries

#### Investigate Job
```yaml
permissions:
  contents: read  # Read-only
```
Cannot:
- ❌ Modify code
- ❌ Deploy changes
- ❌ Access secrets
- ❌ Write to issues/PRs

Can:
- ✅ Read repository files
- ✅ Analyze logs
- ✅ Call read-only APIs
- ✅ Create audit events

#### Act Job
```yaml
permissions:
  contents: write  # Scoped write access
  issues: write
```
Cannot:
- ❌ Run without approval
- ❌ Access unrelated resources
- ❌ Modify workflow files

Can:
- ✅ Execute approved action
- ✅ Update specific resources
- ✅ Create audit events

---

## 🎮 Usage

### Manual Trigger (Common Case)

1. Go to **Actions** → **Agent Runtime - Investigate & Act**
2. Click **Run workflow**
3. Fill in inputs:
   - **Trigger Source**: `manual`
   - **Trace ID**: `trace-$(date +%s)` (or use existing)
   - **Resource**: Target resource (e.g., `service-api-prod`)
   - **Action Context**: Optional JSON context
4. Click **Run workflow**

### The Workflow Will:
1. ✅ **Investigate** - Analyze the resource (read-only)
2. ⏸️ **Wait** - Pause for human approval
3. 🔔 **Notify** - Send notification to approvers
4. ✅ **Act** - Execute action after approval
5. 📊 **Summarize** - Create complete summary

### Approval Process

1. Workflow runs investigate job
2. Investigation report is uploaded as artifact
3. Workflow pauses at `approve` job
4. Approver reviews:
   - Investigation findings
   - Recommended action
   - Risk assessment
5. Approver approves/rejects via GitHub UI
6. On approval, `act` job executes

---

## 🔐 Security Model

### Ephemeral Credentials

Each job gets fresh credentials that expire at job end:

```yaml
jobs:
  investigate:
    permissions:
      contents: read  # Expires after job
  
  act:
    permissions:
      contents: write  # Different token, expires after job
```

**Key Properties**:
- ✅ Time-bounded (job lifetime)
- ✅ Scope-limited (job permissions)
- ✅ Non-transferable (between jobs)
- ✅ Automatically rotated (each run)

### Environment Protection

```yaml
approve:
  environment:
    name: agent-approval  # Configured in repo settings
```

**Protection Rules** (configured in GitHub):
- 🔒 Required reviewers (1+)
- ⏰ Wait timer (optional delay)
- 🌳 Deployment branches (limit to main/prod)
- 📋 Custom deployment protection rules

---

## 📝 Audit Trail

### AIMgentix Integration

All actions are logged to AIMgentix with:

```json
{
  "trace_id": "trace-1738444624",
  "agent_instance_id": "gh-actions-1234567890",
  "actor": "agent",
  "action_type": "tool_call",
  "resource": "service-api-prod",
  "status": "success",
  "latency_ms": 342,
  "metadata": {
    "workflow_run_id": "1234567890",
    "job_name": "investigate",
    "trigger_source": "manual"
  }
}
```

### Trace ID Correlation

Use the same `trace_id` across:
- 🔹 Workflow input
- 🔹 All AIMgentix events
- 🔹 External alerts/incidents
- 🔹 SIEM logs

**Query**: Look up all events for a workflow run:
```bash
# Via AIMgentix UI
trace_id: trace-1738444624

# Or via API
GET /v1/traces/trace-1738444624/events
```

---

## 🔄 Event Streams

### Trigger Sources

#### 1. Manual (Development/Operations)
```yaml
on:
  workflow_dispatch:
    inputs: { ... }
```

**Use Cases**:
- Ad-hoc investigations
- Manual remediation
- Testing workflows

#### 2. Alert-Based (Future)
```yaml
on:
  repository_dispatch:
    types: [alert-triggered]
```

**Use Cases**:
- Automated incident response
- Self-healing systems
- Alert-driven remediation

#### 3. Scheduled (Proactive)
```yaml
on:
  schedule:
    - cron: '*/30 * * * *'
```

**Use Cases**:
- Health checks
- Proactive maintenance
- Periodic validation

---

## 🎯 Use Cases

### 1. Service Restart
**Scenario**: API service is unhealthy

**Flow**:
1. Alert → Workflow triggered
2. Investigate → Check service health, logs, dependencies
3. Recommend → "Restart service-api-prod"
4. Approve → Human reviews investigation
5. Act → Restart service via API

**Audit Trail**: Complete trace from alert to resolution

### 2. Configuration Rollback
**Scenario**: Bad config deployed

**Flow**:
1. Manual → Engineer notices issue
2. Investigate → Compare current vs previous config
3. Recommend → "Rollback to version X"
4. Approve → Senior engineer approves
5. Act → Rollback configuration

**Audit Trail**: Who approved, what changed, when

### 3. Security Incident Response
**Scenario**: Suspicious activity detected

**Flow**:
1. Alert → SIEM integration triggers workflow
2. Investigate → Analyze logs, network traffic, user activity
3. Recommend → "Disable user account"
4. Approve → Security team reviews
5. Act → Disable account, rotate credentials

**Audit Trail**: Complete incident timeline

---

## 📚 Architecture Patterns

### Stateless Agents

Agents run as **ephemeral functions**:

```python
def investigate(resource: str, context: dict) -> dict:
    """Stateless investigation function"""
    # 1. Fetch current state
    state = fetch_resource_state(resource)
    
    # 2. Analyze
    findings = analyze(state, context)
    
    # 3. Return recommendation
    return {
        "recommendation": "restart_service",
        "confidence": 0.95,
        "safe_to_proceed": True
    }
```

**Benefits**:
- ✅ No persistent state
- ✅ Testable in isolation
- ✅ Repeatable results
- ✅ Easy to debug

### Approval Gate Patterns

#### Pattern 1: Always Manual
```yaml
approve:
  environment: prod-approval  # Always requires human
```

#### Pattern 2: Auto-Approve Low Risk
```yaml
steps:
  - name: Check Auto-Approval
    run: |
      if [ "$CONFIDENCE" -gt 0.95 ] && [ "$RISK" = "low" ]; then
        echo "Auto-approved"
      else
        echo "Manual approval required" && exit 1
      fi
```

#### Pattern 3: Policy-Based
```yaml
steps:
  - name: Evaluate Policy
    run: python policy_engine.py --findings findings.json
```

---

## 🚧 When NOT to Use GitHub Actions

GitHub Actions is great for v1, but consider alternatives when:

### Use Kubernetes When:
- ⏱️ Need long-running agents (>6 hours)
- 🔄 High concurrency (100+ simultaneous agents)
- 📡 Real-time event processing required
- 🌐 External event streams (webhooks, message queues)

### Use Serverless When:
- ⚡ Sub-second latency required
- 💰 Want pay-per-invocation pricing
- 🔌 Tight integration with cloud services

### Use GitHub Actions When:
- ✅ Starting out (v1/MVP)
- ✅ Infrequent executions (<100/day)
- ✅ Human-in-the-loop required
- ✅ Git-native workflows
- ✅ Approval gates needed

---

## 🎓 Best Practices

### 1. Design for Idempotency
```python
def act(resource: str, action: str):
    # Check if already done
    if is_already_done(resource, action):
        return {"status": "already_done"}
    
    # Do the thing
    execute_action(resource, action)
```

### 2. Fail Open on Audit Failures
```python
try:
    audit_client.capture(event)
except Exception:
    # Don't fail workflow if audit fails
    logger.warning("Audit capture failed")
```

### 3. Include Rollback Info
```python
result = {
    "action": "restart_service",
    "status": "success",
    "rollback_available": True,
    "rollback_command": "restart --version=previous"
}
```

### 4. Use Trace IDs Everywhere
```python
# Generate once, use everywhere
trace_id = f"trace-{int(time.time())}"

# Pass to all systems
workflow_input["trace_id"] = trace_id
audit_event["trace_id"] = trace_id
external_api_call(headers={"X-Trace-ID": trace_id})
```

### 5. Capture Before & After State
```python
# Before
before_state = get_resource_state(resource)
audit_client.capture(event(action="snapshot", state=before_state))

# Action
execute_action(resource)

# After
after_state = get_resource_state(resource)
audit_client.capture(event(action="snapshot", state=after_state))
```

---

## 🔗 Related Documents

- **Spec**: `specs/github-actions-agent-runtime.md` - Technical specification
- **Workflow**: `.github/workflows/agent-investigate-act.yml` - Implementation
- **AIMgentix**: `docs/QUICKSTART.md` - Audit trail setup
- **Architecture**: `docs/ARCHITECTURE.md` - System design

---

## 📊 Comparison: GitHub Actions vs Alternatives

| Feature | GitHub Actions | Kubernetes | Lambda/Serverless |
|---------|----------------|------------|-------------------|
| **Setup Time** | < 10 minutes | Hours/Days | Hours |
| **Infrastructure** | Zero | High | Medium |
| **Approval Gates** | Native | Custom | Custom |
| **Audit Trail** | Native + AIMgentix | Custom | CloudWatch + Custom |
| **Permissions** | Job-level, GitHub-managed | RBAC, Complex | IAM, Role-based |
| **Cost** | Free (public), $0.008/min (private) | $70+/month | Pay-per-invoke |
| **Concurrency** | Medium (20 jobs default) | High (unlimited) | High (1000+) |
| **Long-Running** | Max 6 hours | Unlimited | Max 15 min |
| **Event Sources** | GitHub, Webhook, Schedule | Any | Cloud-native |

**Recommendation**: Start with GitHub Actions, migrate to K8s when you hit limits.

---

## ❓ FAQ

### Q: Can I run agents on self-hosted runners?
**A**: Yes, but ephemeral GitHub-hosted runners are more secure. Self-hosted runners should be:
- Isolated (no shared state)
- Ephemeral (destroyed after each job)
- Monitored (audit all activity)

### Q: What about secrets management?
**A**: Use GitHub environment secrets:
- Scoped to specific environments
- Only accessible to approved jobs
- Automatically masked in logs

### Q: How do I handle long-running investigations?
**A**: Break into multiple jobs:
```yaml
investigate-phase-1:
  # Quick checks
investigate-phase-2:
  needs: investigate-phase-1
  # Deeper analysis
```

### Q: Can I integrate with external alerting systems?
**A**: Yes, use `repository_dispatch`:
```bash
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/dispatches \
  -d '{"event_type":"alert-triggered","client_payload":{"resource":"api-prod"}}'
```

### Q: How do I test workflows locally?
**A**: Use [`act`](https://github.com/nektos/act):
```bash
act workflow_dispatch -e event.json
```

### Q: What about compliance (SOC2, HIPAA, etc.)?
**A**: GitHub Actions provides:
- Audit logs (90 days retained)
- Approval gates (compliance workflows)
- Environment protection (change control)
- Secret scanning (prevent leaks)

---

## 🎯 Next Steps

1. **Review the workflow**: `.github/workflows/agent-investigate-act.yml`
2. **Set up environment protection**: GitHub Settings → Environments → Create "agent-approval"
3. **Test the workflow**: Actions → Run workflow
4. **Configure AIMgentix**: Follow `docs/QUICKSTART.md`
5. **Customize for your use case**: Modify investigate/act logic

---

**Built with ❤️ for CI/CD-native agent execution**
