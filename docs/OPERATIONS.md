# 🚀 Sentinel Operations Guide

**Production deployment, monitoring, and troubleshooting**

---

## 📋 Prerequisites

- Python 3.8+
- 2GB RAM minimum
- 10GB disk space
- Network access for API endpoints

---

## 🏃 Running in Production

### **Option 1: Docker Compose** (Recommended)

Coming soon - see [GitHub Issue #1]

### **Option 2: Systemd Service** (Linux)

**1. Create service file** (`/etc/systemd/system/sentinel-api.service`):
```ini
[Unit]
Description=Sentinel Audit API
After=network.target

[Service]
Type=simple
User=sentinel
WorkingDirectory=/opt/sentinel/backend
Environment="PATH=/opt/sentinel/venv/bin"
ExecStart=/opt/sentinel/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**2. Enable and start**:
```bash
sudo systemctl enable sentinel-api
sudo systemctl start sentinel-api
sudo systemctl status sentinel-api
```

### **Option 3: Cloud Deployment**

#### **AWS (Elastic Beanstalk)**
```bash
# Install EB CLI
pip install awsebcli

# Initialize
cd backend
eb init -p python-3.11 sentinel-api

# Deploy
eb create sentinel-prod
eb open
```

#### **Google Cloud Run**
```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/sentinel-api

# Deploy
gcloud run deploy sentinel-api \
  --image gcr.io/PROJECT_ID/sentinel-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### **Azure App Service**
```bash
# Create resource group
az group create --name sentinel-rg --location eastus

# Create app service plan
az appservice plan create --name sentinel-plan --resource-group sentinel-rg --sku B1 --is-linux

# Deploy
az webapp up --name sentinel-api --resource-group sentinel-rg --runtime "PYTHON:3.11"
```

---

## 📊 Monitoring

### **Health Checks**

**Endpoint**: `GET /`

**Expected Response**:
```json
{
  "service": "Sentinel Audit API",
  "status": "operational",
  "version": "0.1.0"
}
```

**Monitoring Script**:
```bash
#!/bin/bash
# /opt/sentinel/healthcheck.sh

ENDPOINT="http://localhost:8000"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)

if [ $RESPONSE -eq 200 ]; then
    echo "✅ Sentinel API is healthy"
    exit 0
else
    echo "❌ Sentinel API is down (HTTP $RESPONSE)"
    exit 1
fi
```

### **Metrics to Track**

1. **API Latency** - p50, p95, p99 response times
2. **Event Throughput** - Events/second ingested
3. **Error Rate** - Failed event captures
4. **Database Size** - Disk usage growth
5. **SDK Retry Rate** - Failed API calls from SDK

### **Logging**

**Backend logs**:
```bash
# View logs
journalctl -u sentinel-api -f

# Or if using Docker
docker logs -f sentinel-api
```

**Log levels**:
- `INFO` - Normal operations
- `WARNING` - Retries, buffer full
- `ERROR` - Failed to store events

---

## 💾 Database Management

### **Backup (SQLite)**

```bash
# Daily backup script
#!/bin/bash
# /opt/sentinel/backup.sh

DB_PATH="/opt/sentinel/backend/sentinel_audit.db"
BACKUP_DIR="/opt/sentinel/backups"
DATE=$(date +%Y%m%d_%H%M%S)

sqlite3 $DB_PATH ".backup '$BACKUP_DIR/sentinel_$DATE.db'"
echo "✅ Backup created: sentinel_$DATE.db"

# Keep only last 7 days
find $BACKUP_DIR -name "sentinel_*.db" -mtime +7 -delete
```

**Cron job** (`crontab -e`):
```
0 2 * * * /opt/sentinel/backup.sh
```

### **Migration to PostgreSQL** (Future)

When you outgrow SQLite:

```bash
# Export from SQLite
sqlite3 sentinel_audit.db .dump > export.sql

# Import to PostgreSQL
psql -U sentinel -d sentinel_db -f export.sql
```

Update `backend/app/db.py`:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/sentinel_db")
```

---

## 🔧 Troubleshooting

### **Problem: API returns 500 errors**

**Check**:
```bash
# View recent errors
journalctl -u sentinel-api --since "10 minutes ago" | grep ERROR

# Check database permissions
ls -la /opt/sentinel/backend/sentinel_audit.db
```

**Fix**:
```bash
# Ensure correct ownership
sudo chown sentinel:sentinel /opt/sentinel/backend/sentinel_audit.db
```

### **Problem: Events not appearing in UI**

**Check**:
1. Backend is running: `curl http://localhost:8000`
2. Events are being captured: `curl http://localhost:8000/v1/agents/demo-agent-001/events`
3. CORS is enabled (check browser console)

**Fix**:
```python
# In backend/app/main.py, ensure CORS is configured:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Problem: SDK retries failing**

**Check SDK logs**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Common causes**:
- Backend not reachable (firewall, network)
- Backend overloaded (increase resources)
- Database locked (SQLite concurrency limit)

---

## 🔐 Security Hardening

### **1. Enable HTTPS**

Use a reverse proxy (nginx):

```nginx
server {
    listen 443 ssl;
    server_name sentinel.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/sentinel.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sentinel.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **2. Add API Authentication** (Future)

```python
# backend/app/auth.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != os.getenv("API_TOKEN"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials
```

### **3. Rate Limiting** (Future)

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/v1/events")
@limiter.limit("100/minute")
async def capture_event(...):
    ...
```

---

## 📈 Scaling

### **When to Scale**

- API latency > 500ms
- Event throughput > 1000/sec
- Database size > 10GB
- CPU usage > 80%

### **Horizontal Scaling**

1. **Load Balancer** - Distribute traffic across multiple API instances
2. **Database** - Migrate to PostgreSQL or DynamoDB
3. **Caching** - Add Redis for frequently accessed events
4. **Event Streaming** - Use Kafka/Kinesis for high throughput

---

## 📞 Support

- 📧 Email: [your-email]
- 🐛 Issues: [GitHub Issues]
- 💬 Discussions: [GitHub Discussions]

