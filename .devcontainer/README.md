# 🐳 Sentinel Dev Container

**One-click development environment for Sentinel Audit**

---

## 🚀 Quick Start

### **Option 1: GitHub Codespaces** (Easiest)

1. Go to the GitHub repo
2. Click **Code** → **Codespaces** → **Create codespace on main**
3. Wait ~2 minutes for setup
4. Run `start-api` in the terminal
5. Open `demo/ui/index.html` in the browser

### **Option 2: VS Code Dev Containers** (Local)

**Prerequisites**:
- Docker Desktop installed
- VS Code with "Dev Containers" extension

**Steps**:
1. Open this repo in VS Code
2. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
3. Select "Dev Containers: Reopen in Container"
4. Wait ~2 minutes for setup
5. Run `start-api` in the terminal

---

## 📦 What's Included

- ✅ Python 3.11
- ✅ Node.js 18 (for future frontend work)
- ✅ Git
- ✅ All Python dependencies pre-installed
- ✅ Sentinel SDK installed in development mode
- ✅ VS Code extensions (Python, linting, formatting)
- ✅ Helpful shell aliases

---

## 🔧 Helpful Aliases

The dev container includes these pre-configured aliases:

```bash
start-api      # Start the FastAPI backend on port 8000
run-demo       # Run the demo agent
test-api       # Test API health check
view-events    # View captured events (pretty-printed JSON)
```

---

## 🌐 Port Forwarding

The dev container automatically forwards these ports:

- **8000** - Sentinel API (FastAPI backend)
- **3000** - Reserved for future UI server

You can access them at:
- `http://localhost:8000` (or the Codespaces URL)

---

## 🛠️ Customization

### **Add More Extensions**

Edit `.devcontainer/devcontainer.json`:

```json
"extensions": [
  "ms-python.python",
  "your-extension-id"
]
```

### **Change Python Version**

Edit `.devcontainer/devcontainer.json`:

```json
"image": "mcr.microsoft.com/devcontainers/python:3.12"
```

### **Add System Packages**

Edit `.devcontainer/setup.sh`:

```bash
sudo apt-get update
sudo apt-get install -y your-package
```

---

## 🐛 Troubleshooting

### **Problem: Container fails to build**

**Solution**: Rebuild the container
```bash
# In VS Code
Cmd+Shift+P → "Dev Containers: Rebuild Container"
```

### **Problem: Ports not forwarding**

**Solution**: Manually forward ports
```bash
# In VS Code
Cmd+Shift+P → "Forward a Port" → Enter 8000
```

### **Problem: SDK import fails**

**Solution**: Reinstall SDK
```bash
cd /workspaces/ondemand-iam-agentic-ai/sdk
pip install -e .
```

---

## 📚 Learn More

- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [GitHub Codespaces](https://github.com/features/codespaces)
- [Dev Container Specification](https://containers.dev/)

---

**Built with ❤️ for instant development**

