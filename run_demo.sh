#!/bin/bash

# Sentinel Demo Runner
# This script sets up and runs the complete demo

set -e

echo "🛡️  Sentinel Audit - Demo Setup"
echo "================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Step 1: Install backend dependencies
echo "📦 Step 1: Installing backend dependencies..."
cd backend
pip install -q -r requirements.txt
cd ..
echo "✅ Backend dependencies installed"
echo ""

# Step 2: Install SDK
echo "📦 Step 2: Installing SDK..."
cd sdk
pip install -q -e .
cd ..
echo "✅ SDK installed"
echo ""

# Step 3: Install demo dependencies
echo "📦 Step 3: Installing demo dependencies..."
cd demo
pip install -q -r requirements.txt
cd ..
echo "✅ Demo dependencies installed"
echo ""

# Step 4: Start backend in background
echo "🚀 Step 4: Starting backend API..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
echo "✅ Backend started (PID: $BACKEND_PID)"
echo ""

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 3

# Test backend
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Backend is ready!"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo ""

# Step 5: Run demo agent
echo "🤖 Step 5: Running demo agent..."
echo ""
cd demo
python3 demo_agent.py
cd ..
echo ""

# Step 6: Instructions
echo "================================"
echo "✨ Demo Complete!"
echo ""
echo "📊 View audit trail:"
echo "   API: http://localhost:8000/v1/agents/demo-agent-001/events"
echo "   UI:  Open demo/ui/index.html in your browser"
echo ""
echo "🛑 To stop the backend:"
echo "   kill $BACKEND_PID"
echo ""
echo "================================"

# Keep script running so backend stays up
echo "Press Ctrl+C to stop the backend and exit..."
wait $BACKEND_PID

