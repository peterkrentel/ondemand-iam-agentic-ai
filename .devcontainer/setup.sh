#!/bin/bash

# AIMgentix Dev Container Setup Script
# This runs automatically when the dev container is created

set -e

echo "🛡️  Setting up AIMgentix development environment..."
echo ""

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd /workspaces/ondemand-iam-agentic-ai/backend
pip install -q -r requirements.txt
echo "✅ Backend dependencies installed"
echo ""

# Install SDK in development mode
echo "📦 Installing AIMgentix SDK..."
cd /workspaces/ondemand-iam-agentic-ai/sdk
pip install -q -e .
echo "✅ SDK installed"
echo ""

# Install demo dependencies
echo "📦 Installing demo dependencies..."
cd /workspaces/ondemand-iam-agentic-ai/demo
pip install -q -r requirements.txt
echo "✅ Demo dependencies installed"
echo ""

# Verify installation
echo "🧪 Verifying installation..."
python -c "from aimgentix import AuditClient; print('✅ AIMgentix SDK import successful')"
echo ""

# Create helpful aliases
echo "📝 Creating helpful aliases..."
cat >> ~/.bashrc << 'EOF'

# AIMgentix aliases
alias start-api='cd /workspaces/ondemand-iam-agentic-ai/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload'
alias run-demo='cd /workspaces/ondemand-iam-agentic-ai/demo && python demo_agent.py'
alias test-api='curl http://localhost:8000'
alias view-events='curl http://localhost:8000/v1/agents/demo-agent-001/events | python -m json.tool'

EOF
echo "✅ Aliases created"
echo ""

# Print welcome message
cat << 'EOF'
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   🛡️  AIMgentix - Development Environment Ready!          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

📚 Quick Start:

  1. Start the API:
     $ start-api

  2. Run the demo (in a new terminal):
     $ run-demo

  3. View events:
     $ view-events

  4. Open the UI:
     Open demo/ui/index.html in the browser

📖 Documentation:
  - docs/QUICKSTART.md - Getting started guide
  - docs/ARCHITECTURE.md - System design
  - docs/OPERATIONS.md - Production deployment
  - README.md - Project overview

🔗 Helpful Commands:
  - start-api      Start the FastAPI backend
  - run-demo       Run the demo agent
  - test-api       Test API health
  - view-events    View captured events

Happy coding! 🚀

EOF

