# 🛡️ AIMgentix - Agent Audit Trail

**Lightweight audit layer for AI agents. Privacy-first. Production-ready. CI/CD-native.**

---

## 🎯 What is This?

AIMgentix captures what your AI agents do - tool calls, API requests, file access - and gives you a complete audit trail.

**The Problem**: Enterprises are deploying AI agents with no visibility into what they're doing. Security teams are nervous. Compliance teams are blocked.

**The Solution**: A lightweight audit layer that sits between your agents and your systems.

---

## 🚀 **NEW: GitHub Actions as Agent Runtime**

**Run agents as CI/CD workflows with built-in permission gates and approval workflows.**

```yaml
Investigate (read-only) → Approve (human gate) → Act (elevated permissions)
```

**Why GitHub Actions?**
- ✅ Ephemeral compute - No infrastructure to manage
- ✅ Permission boundaries - Job-level permissions enforced by GitHub
- ✅ Approval gates - Native environment protection
- ✅ Complete audit trail - Git history + AIMgentix events + workflow logs
- ✅ Zero local development - CI/CD-first, no "works on my machine"

**→ [See Full Documentation](docs/GITHUB_ACTIONS_RUNTIME.md)**

**→ [Try the Workflow](.github/workflows/agent-investigate-act.yml)**

---

## ✨ Features

- ✅ **Non-blocking capture** - Doesn't slow down your agents
- ✅ **Privacy-first** - Redacts sensitive data by default
- ✅ **Framework agnostic** - Works with LangChain, AutoGen, CrewAI, custom agents
- ✅ **CI/CD-native runtime** - Run agents as GitHub Actions workflows
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
├── .github/workflows/    # CI/CD + Agent Runtime workflows
│   ├── agent-investigate-act.yml  # Example agent workflow
│   ├── build-test.yml             # CI/CD pipeline
│   └── spec-validation.yml        # Contract testing
├── backend/              # FastAPI audit API
├── sdk/                  # Python SDK
├── demo/                 # Demo agent + UI
├── docs/                 # Documentation
│   └── GITHUB_ACTIONS_RUNTIME.md  # CI/CD runtime guide
├── specs/                # Specifications
│   ├── github-actions-agent-runtime.md  # Workflow spec
│   └── event-schema.md             # Event schema spec
└── mvp-master-plan.md   # Full product roadmap
```

---

## 🎯 Agent Runtime Patterns

### Pattern 1: GitHub Actions (Recommended for v1)

Run agents as CI/CD workflows with approval gates:

```yaml
jobs:
  investigate:
    permissions:
      contents: read  # Read-only
    steps:
      - run: python agent.py investigate
  
  approve:
    environment: prod-approval  # Human gate
    needs: investigate
  
  act:
    permissions:
      contents: write  # Elevated
    needs: approve
    steps:
      - run: python agent.py act
```

**Use when**: Starting out, human-in-the-loop required, infrequent executions

**Benefits**: Zero infrastructure, native approvals, complete audit trail

**→ [Full Guide](docs/GITHUB_ACTIONS_RUNTIME.md)**

### Pattern 2: Kubernetes (For scale)

Run agents as long-running pods with policy engine:

**Use when**: High concurrency, real-time events, multi-agent orchestration

**Migration**: Start with GitHub Actions, migrate when you hit limits

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
- [x] GitHub Actions agent runtime (investigate → approve → act)
- [x] Spec-driven development (event schema, workflow contracts)
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
3. **GitHub Actions agent runtime** - run agents as CI/CD workflows, no local dev needed
4. **Upgrade GitHub account** - for more Codespaces hours if you prefer cloud development

### **Why use GitHub Actions for agents?**

If you hate local development, GitHub Actions is perfect:
- ✅ No local setup required
- ✅ Ephemeral compute (no state to manage)
- ✅ Built-in permissions and approval gates
- ✅ Complete audit trail via git + AIMgentix
- ✅ CI/CD-native (no "works on my machine")

See [docs/GITHUB_ACTIONS_RUNTIME.md](docs/GITHUB_ACTIONS_RUNTIME.md) for details.

---

## 🤝 Contributing

This is an early-stage project. Feedback and contributions welcome!

---

## 📄 License

MIT License - Copyright 2026 Peter Krentel

---

## 📚 Documentation

### Getting Started
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[GITHUB_ACTIONS_RUNTIME.md](docs/GITHUB_ACTIONS_RUNTIME.md)** - CI/CD-native agent execution ⭐ NEW

### Architecture & Design
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design with diagrams
- **[OPERATIONS.md](docs/OPERATIONS.md)** - Production deployment guide

### Specifications
- **[specs/event-schema.md](specs/event-schema.md)** - Event schema contract
- **[specs/github-actions-agent-runtime.md](specs/github-actions-agent-runtime.md)** - Workflow contract ⭐ NEW
- **[specs/SPEC_POLICY.md](specs/SPEC_POLICY.md)** - Spec-driven development guide

### Development
- **[Dev Container README](.devcontainer/README.md)** - One-click dev environment
- **[CONTRACT_TESTING.md](docs/CONTRACT_TESTING.md)** - Testing approach

## 🔗 Links

- **Issues**: [GitHub Issues](https://github.com/peterkrentel/ondemand-iam-agentic-ai/issues)

---

**Built with ❤️ for the agent IAM community**
