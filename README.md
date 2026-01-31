# 🛡️ OnDemand IAM Agentic AI - Agent Audit Trail

**Lightweight audit layer for AI agents. Privacy-first. Production-ready.**

---

## 🎯 What is This?

OnDemand IAM Agentic AI captures what your AI agents do - tool calls, API requests, file access - and gives you a complete audit trail.

**The Problem**: Enterprises are deploying AI agents with no visibility into what they're doing. Security teams are nervous. Compliance teams are blocked.

**The Solution**: A lightweight audit layer that sits between your agents and your systems.

---

## ✨ Features

- ✅ **Non-blocking capture** - Doesn't slow down your agents
- ✅ **Privacy-first** - Redacts sensitive data by default
- ✅ **Framework agnostic** - Works with LangChain, AutoGen, CrewAI, custom agents
- ✅ **Simple integration** - 3 lines of code
- ✅ **Beautiful UI** - Real-time audit trail visualization
- ✅ **Production-ready** - Buffering, retry logic, graceful degradation

---

## 🚀 Quick Start

### **Option 1: One-Click Dev Container** (Recommended)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main)

Or open in VS Code with Dev Containers extension - everything is pre-configured!

See [.devcontainer/README.md](.devcontainer/README.md) for details.

### **Option 2: Local Setup**

**1. Start the backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**2. Install the SDK:**
```bash
cd sdk
pip install -e .
```

**3. Run the demo:**
```bash
cd demo
pip install -r requirements.txt
python demo_agent.py
```

**4. View the audit trail:**
Open `demo/ui/index.html` in your browser

**Full guide**: See [docs/QUICKSTART.md](docs/QUICKSTART.md)

---

## 📦 What's Inside

```
ondemand-iam-agentic-ai/
├── backend/              # FastAPI audit API
├── sdk/                  # Python SDK
├── demo/                 # Demo agent + UI
├── docs/                 # Documentation
└── mvp-master-plan.md   # Full product roadmap
```

---

## 🔧 Integration Example

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
    latency_ms=342
)

audit_client.capture(event)
```

---

## 🎬 Demo

![OnDemand IAM Agentic AI Dashboard](https://via.placeholder.com/800x400?text=OnDemand+IAM+Agentic+AI+Audit+Dashboard)

---

## 🗺️ Roadmap

**Week 1** (Current):
- [x] Core MVP - Backend, SDK, Demo
- [ ] Customer validation (5 conversations)

**Week 2**:
- [ ] Iterate based on feedback
- [ ] First pilot customer OR thought leadership content

**Future** (based on customer demand):
- [ ] Policy generation from audit trails
- [ ] Anomaly detection
- [ ] SIEM integrations
- [ ] Multi-tenant support

See [mvp-master-plan.md](mvp-master-plan.md) for full details.

---

## 🤝 Contributing

This is an early-stage project. Feedback and contributions welcome!

---

## 📄 License

MIT License - Copyright 2026 Peter Krentel

---

## 📚 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design with diagrams
- **[OPERATIONS.md](docs/OPERATIONS.md)** - Production deployment guide
- **[Dev Container README](.devcontainer/README.md)** - One-click dev environment

## 🔗 Links

- **Issues**: [GitHub Issues](https://github.com/peterkrentel/ondemand-iam-agentic-ai/issues)

---

**Built with ❤️ for the agent IAM community**
