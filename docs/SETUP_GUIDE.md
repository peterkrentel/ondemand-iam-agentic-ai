# Setting Up GitHub Actions Agent Runtime

This guide walks through setting up the GitHub Actions agent runtime with approval gates and environment protection.

---

## Prerequisites

- Repository with admin access
- AIMgentix backend running (optional, for audit trail)
- Python 3.8+ (already available in GitHub-hosted runners)

---

## Step 1: Create Environment Protection

GitHub environment protection provides the approval gate in the workflow.

### 1.1 Navigate to Environment Settings

1. Go to your repository on GitHub
2. Click **Settings** → **Environments**
3. Click **New environment**
4. Name it: `agent-approval`
5. Click **Configure environment**

### 1.2 Configure Protection Rules

Add these protection rules:

#### Required Reviewers
- ✅ Check **Required reviewers**
- Add 1 or more team members who can approve agent actions
- Recommended: At least 2 reviewers for production

#### Wait Timer (Optional)
- Set a wait timer (e.g., 5 minutes) to prevent immediate execution
- Gives reviewers time to see the notification

#### Deployment Branches (Recommended)
- ✅ Limit to **Selected branches**
- Add `main` (or your production branch)
- Prevents agent runs from feature branches

### 1.3 Save Configuration

Click **Save protection rules**

---

## Step 2: Test the Workflow

### 2.1 Manual Trigger

1. Go to **Actions** tab
2. Select **Agent Runtime - Investigate & Act**
3. Click **Run workflow**
4. Fill in inputs:
   - **Trigger Source**: `manual`
   - **Trace ID**: `trace-test-001`
   - **Resource**: `test-service-api`
   - **Action Context**: `{"priority": "high"}`
5. Click **Run workflow**

### 2.2 Observe the Flow

1. **Investigate Job**: Runs immediately (read-only)
   - Check logs to see investigation results
   - Download `investigation-report` artifact

2. **Approve Job**: Waits for human approval
   - GitHub sends notification to reviewers
   - Reviewers see investigation findings
   - Reviewers approve/reject

3. **Act Job**: Runs after approval (elevated permissions)
   - Executes the approved action
   - Creates audit trail
   - Uploads action result

---

## Step 3: Integrate with AIMgentix (Optional)

To capture complete audit trails:

### 3.1 Start AIMgentix Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3.2 Add Backend URL as Secret

If your AIMgentix backend requires authentication or is not public:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add new repository secret:
   - Name: `AIMGENTIX_API_URL`
   - Value: `https://your-aimgentix-backend.com`

### 3.3 Update Workflow (If Needed)

The workflow uses environment variables automatically:

```yaml
env:
  AIMGENTIX_API_URL: ${{ secrets.AIMGENTIX_API_URL }}
```

---

## Step 4: Customize for Your Use Case

### 4.1 Modify Investigation Logic

Edit `agent_runner.py` → `investigate()` method:

```python
def investigate(self, resource: str, context: Optional[Dict[str, Any]] = None):
    # Your custom investigation logic
    # Examples:
    # - Query monitoring systems
    # - Check service health
    # - Analyze logs
    # - Check dependencies
    
    # Return investigation result
    return InvestigationResult(...)
```

### 4.2 Modify Action Logic

Edit `agent_runner.py` → `act()` method:

```python
def act(self, resource: str, action: str, context: Optional[Dict[str, Any]] = None):
    # Your custom action logic
    # Examples:
    # - Restart service via API
    # - Deploy configuration
    # - Roll back changes
    # - Execute remediation
    
    # Return action result
    return ActionResult(...)
```

### 4.3 Add New Triggers

#### Alert-Based Trigger

Add to workflow file:

```yaml
on:
  repository_dispatch:
    types: [alert-triggered]
```

Then trigger via API:

```bash
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/owner/repo/dispatches \
  -d '{
    "event_type": "alert-triggered",
    "client_payload": {
      "resource": "api-prod",
      "alert_severity": "high",
      "trace_id": "alert-12345"
    }
  }'
```

#### Scheduled Trigger

Add to workflow file:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
```

---

## Step 5: Production Checklist

Before using in production:

### Security
- [ ] Environment protection configured with required reviewers
- [ ] Deployment branches limited (no feature branches)
- [ ] Secrets properly stored (no hardcoded credentials)
- [ ] Audit trail enabled (AIMgentix integration)

### Testing
- [ ] Test investigate job with read-only permissions
- [ ] Test approval gate (approve and reject scenarios)
- [ ] Test act job with elevated permissions
- [ ] Verify audit events are captured

### Documentation
- [ ] Document investigation logic
- [ ] Document action logic
- [ ] Document approval criteria
- [ ] Create runbook for common scenarios

### Monitoring
- [ ] Set up alerts for workflow failures
- [ ] Monitor audit trail for anomalies
- [ ] Review approved actions regularly
- [ ] Track approval response times

---

## Troubleshooting

### Issue: Workflow Can't Find `agent_runner.py`

**Solution**: Make sure the file is in the repository root:

```bash
ls -la agent_runner.py
```

### Issue: AIMgentix SDK Not Found

**Solution**: Check SDK installation step in workflow:

```yaml
- name: Install AIMgentix SDK
  run: |
    cd sdk
    pip install -e .
```

### Issue: Approval Gate Not Working

**Solution**: Verify environment protection:

1. Settings → Environments → `agent-approval`
2. Check "Required reviewers" is enabled
3. Check reviewers are added
4. Check branch restrictions match your branch

### Issue: Permission Denied in Act Job

**Solution**: Check job-level permissions:

```yaml
act:
  permissions:
    contents: write  # Adjust based on needs
    issues: write
```

### Issue: Audit Events Not Captured

**Solution**: Check AIMgentix backend:

```bash
# Check if backend is running
curl http://localhost:8000/

# Check logs in workflow
# Look for "✅ AIMgentix audit client initialized"
```

---

## Next Steps

1. **Customize**: Modify `agent_runner.py` for your specific use cases
2. **Test**: Run multiple test workflows with different scenarios
3. **Integrate**: Connect to your monitoring/alerting systems
4. **Scale**: Add more workflows for different types of agents
5. **Monitor**: Review audit trails and approval patterns

---

## Example Use Cases

### 1. Service Restart on High Error Rate

**Trigger**: Alert from monitoring system

**Investigation**:
- Check error rate (last 1 hour)
- Verify service health endpoints
- Check dependencies

**Decision**:
- If error rate > 5%: Recommend restart
- If error rate > 10%: Recommend investigation + restart

**Action**:
- Call service API to restart
- Wait for health check
- Verify error rate decreased

### 2. Configuration Rollback

**Trigger**: Manual trigger after deployment

**Investigation**:
- Compare current vs previous config
- Check application logs for errors
- Verify feature flags

**Decision**:
- If errors detected: Recommend rollback
- If healthy: No action needed

**Action**:
- Rollback configuration to previous version
- Restart affected services
- Verify health

### 3. Scale Up Resources

**Trigger**: Scheduled check (every 6 hours)

**Investigation**:
- Check CPU/memory usage
- Check request latency
- Predict load trends

**Decision**:
- If usage > 80%: Recommend scale up
- If usage < 20%: Recommend scale down

**Action**:
- Update autoscaling configuration
- Trigger scaling event
- Verify new capacity online

---

## Reference

- **Workflow Spec**: `specs/github-actions-agent-runtime.md`
- **Full Documentation**: `docs/GITHUB_ACTIONS_RUNTIME.md`
- **Agent Runner**: `agent_runner.py`
- **Workflow File**: `.github/workflows/agent-investigate-act.yml`

---

**Need help?** Open an issue or check the documentation.
