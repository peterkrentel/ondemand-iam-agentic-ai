# 🚀 OnDemand IAM Agentic AI - Quick Start Guide

**Agent Audit Trail Capture in 5 Minutes**

---

## What is This?

OnDemand IAM Agentic AI is a lightweight audit layer for AI agents. It captures:
- ✅ What tools agents use
- ✅ What resources they access
- ✅ When and how long operations take
- ✅ Success/failure status

**Privacy-first**: Redacts sensitive data by default.

---

## Prerequisites

- Python 3.8+
- pip

---

## Step 1: Start the Backend

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

**Test it:**
```bash
curl http://localhost:8000
```

You should see:
```json
{
  "service": "OnDemand IAM Agentic AI API",
  "status": "operational",
  "version": "0.1.0"
}
```

---

## Step 2: Install the SDK

```bash
# Navigate to SDK directory
cd ../sdk

# Install in development mode
pip install -e .
```

---

## Step 3: Run the Demo Agent

```bash
# Navigate to demo directory
cd ../demo

# Install demo dependencies
pip install -r requirements.txt

# Run the demo
python demo_agent.py
```

You should see:
```
🚀 Starting OnDemand IAM Agentic AI Demo Agent
📋 Agent Instance ID: demo-agent-001
🔍 Trace ID: trace-20260125-103000

✅ Audit client initialized
✅ Created agent with 2 instrumented tools

🤖 Simulating agent actions...

1️⃣  Performing web search...
   ✅ Search completed (1234 chars)

2️⃣  Reading file...
   ✅ File read completed

💾 Flushing audit events...
   ✅ Events flushed to API

✨ Demo complete!
```

---

## Step 4: View the Audit Trail

### Option A: API Endpoint

```bash
curl http://localhost:8000/v1/agents/demo-agent-001/events
```

### Option B: Web Dashboard

1. Open `demo/ui/index.html` in your browser
2. Enter Agent ID: `demo-agent-001`
3. Click "Load Events"

You'll see a beautiful timeline of all agent actions!

---

## Step 5: Instrument Your Own Agent

```python
from ondemand_iam_agentic_ai import AuditClient, AuditEvent, ActorType, ActionType, EventStatus

# Initialize client
audit_client = AuditClient(api_url="http://localhost:8000")

# Capture an event
event = AuditEvent(
    agent_instance_id="my-agent-001",
    trace_id="trace-abc123",
    actor=ActorType.AGENT,
    action_type=ActionType.TOOL_CALL,
    resource="web_search",
    status=EventStatus.SUCCESS,
    latency_ms=342,
    metadata={"query": "[REDACTED]"}
)

audit_client.capture(event)
audit_client.flush()
```

---

## Architecture

```
┌─────────────┐
│  Your Agent │
└──────┬──────┘
       │ (uses SDK)
       ▼
┌─────────────────┐
│  OnDemand IAM   │  ← Non-blocking, buffered, retry logic
│      SDK        │
└──────┬──────────┘
       │ (HTTP)
       ▼
┌─────────────────┐
│  FastAPI Backend│  ← POST /v1/events, GET /v1/agents/{id}/events
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  SQLite DB      │  ← Audit trail storage
└─────────────────┘
```

---

## Next Steps

1. **Instrument your production agents** - Add the SDK to your LangChain/AutoGen/CrewAI agents
2. **Deploy the backend** - Run on AWS/GCP/Azure
3. **Add authentication** - Secure the API endpoints
4. **Integrate with SIEM** - Send events to Splunk/Datadog
5. **Build policies** - Define what agents can/cannot do

---

## Troubleshooting

**Problem**: `Connection refused` when running demo
**Solution**: Make sure the backend is running (`uvicorn app.main:app --reload`)

**Problem**: No events showing in UI
**Solution**: Check the browser console for CORS errors. Make sure backend is running on `localhost:8000`

**Problem**: Import errors in demo
**Solution**: Make sure you installed the SDK (`cd sdk && pip install -e .`)

---

## Support

- 📧 Email: [your-email]
- 🐛 Issues: [GitHub Issues]
- 💬 Discussions: [GitHub Discussions]

---

**Built with ❤️ for the agent IAM community**

