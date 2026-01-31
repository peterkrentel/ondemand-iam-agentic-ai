# 🛡️ AIMgentix - Agent Audit Trail

**Lightweight audit layer for AI agents. Privacy-first. Production-ready.**

---

## 🎯 What is This?

AIMgentix captures what your AI agents do - tool calls, API requests, file access - and gives you a complete audit trail.

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
aimgentix/
├── backend/              # FastAPI audit API
├── sdk/                  # Python SDK
├── demo/                 # Demo agent + UI
├── docs/                 # Documentation
└── mvp-master-plan.md   # Full product roadmap
```

---

## 🔧 Integration Example

```python
from aimgentix import AuditClient, AuditEvent, ActorType, ActionType, EventStatus

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

![AIMgentix Dashboard](https://via.placeholder.com/800x400?text=AIMgentix+Audit+Dashboard)

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

## ❓ FAQ

### **Does AIMgentix have any usage limits or pricing?**

**No!** AIMgentix is:
- ✅ Completely open source (MIT License)
- ✅ No usage limits or rate limiting
- ✅ No premium tiers or paid features  
- ✅ Runs entirely on your own infrastructure

You control all aspects of deployment and can handle unlimited audit events.

### **What does "2 premium requests" mean in GitHub Codespaces?**

This refers to **GitHub Codespaces usage limits**, not AIMgentix:

- GitHub's free tier includes 120 core-hours/month (≈60 hours on a 2-core machine)
- When you exceed this, GitHub may prompt for paid Codespaces usage
- **Alternative**: Use local development (VS Code Dev Containers or direct setup) - completely free with no limits

[Learn more about GitHub Codespaces billing](https://docs.github.com/en/billing/managing-billing-for-github-codespaces/about-billing-for-github-codespaces)

### **How do I avoid Codespaces limits?**

Three options:
1. **VS Code Dev Containers** (locally with Docker) - unlimited, free
2. **Regular local setup** - no containers needed, see Quick Start above
3. **Upgrade GitHub account** - for more Codespaces hours if you prefer cloud development

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
