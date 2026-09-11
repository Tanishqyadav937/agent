# Local SQLite Chroma Setup Guide

Complete guide to running Chroma with persistent SQLite locally for development.

## Overview

Instead of using Chroma Cloud, you can run Chroma locally with:
- **SQLite database** (persistent, survives restarts)
- **HTTP server** on localhost:8000
- **Automatic data persistence** to disk
- **Zero cloud dependencies** (great for development)

---

## Option 1: Docker (Recommended - Easiest)

### 1.1 Start Local Chroma Server (Docker)

```bash
# Start Chroma server with persistent SQLite
docker run -p 8000:8000 -v chroma-data:/chroma/chroma-data chromadb/chroma

# Expected output:
# Loaded 0 collections
# Uvicorn running on http://0.0.0.0:8000
```

### 1.2 Verify Chroma is Running

```bash
# In another terminal, test the connection
curl http://localhost:8000/api/v1/heartbeat

# Should return: OK
```

### 1.3 Update .env for Local Development

```bash
# .env (development)
CHROMA_URL=http://localhost:8000
# No CHROMA_API_KEY needed for local

# All other vars as before:
LLM_PROVIDER=local
OLLAMA_MODEL=qwen2.5:7b-instruct
EMBEDDING_MODEL=mxbai-embed-large
```

### 1.4 Start Your Backend

```bash
npm start

# Expected: Backend connects to local Chroma
# [Chroma] URL: http://localhost:8000
# [Memory] Chroma initialized successfully
```

---

## Option 2: Python Direct Install (Alternative)

If you prefer running Chroma without Docker:

### 2.1 Install Chroma CLI

```bash
# Install via pip
pip install chroma

# Or use UV (faster)
uv pip install chroma
```

### 2.2 Start Chroma Server

```bash
# Simple start (in-memory)
chroma run --host 0.0.0.0 --port 8000

# With persistent SQLite (recommended)
chroma run --host 0.0.0.0 --port 8000 --path ./chroma_data

# Expected output:
# Uvicorn running on http://0.0.0.0:8000
```

### 2.3 Verify Setup

Same as Option 1.2-1.4 above

---

## Option 3: Node.js Persistent Client (Advanced)

Use Chroma's persistent Python SDK directly from Node.js:

### 3.1 Install Chroma Node Package

```bash
npm install chromadb
```

### 3.2 Update server.js for Persistent Local

Replace the Chroma initialization in server.js:

```javascript
// OLD (always connects to server):
const chromaClient = new ChromaClient({
  path: 'http://localhost:8000'
});

// NEW (persistent local SQLite):
const { PersistentClient } = require('chromadb');

const chromaClient = new PersistentClient({
  path: './chroma-data'  // SQLite database location
});
```

**Advantages**:
- No need to run separate Chroma server
- SQLite data stored in `./chroma-data` directory
- Survives app restarts
- Lower memory usage

**Trade-offs**:
- Python runtime required (chromadb runs on Python)
- Slightly slower than in-process (through Node.js bridge)

---

## Data Persistence Comparison

| Method | Data Location | Persists? | Setup | Use Case |
|--------|---------------|-----------|-------|----------|
| **Docker Volume** | `chroma-data:/` volume | ✅ Yes | 1 command | Recommended |
| **Python Direct** | `./chroma_data/` local | ✅ Yes | pip install | No Docker |
| **Persistent Client** | `./chroma-data/` | ✅ Yes | Node.js config | Fully integrated |
| **In-Memory** | RAM only | ❌ No | Default | Testing only |

---

## Recommended Setup for Development

### Quick Start (Docker)

```bash
# Terminal 1: Start Chroma server
docker run -p 8000:8000 -v chroma-data:/chroma/chroma-data chromadb/chroma

# Terminal 2: Start backend
npm start

# Terminal 3: Test
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "test", "user_input": "Hello"}'
```

### Full Stack

```bash
# Terminal 1: Local Chroma server
docker run -p 8000:8000 -v chroma-data:/chroma/chroma-data chromadb/chroma

# Terminal 2: Ollama (if LLM_PROVIDER=local)
ollama serve

# Terminal 3: Your backend
npm start

# Terminal 4: Test/Development
npm run dev
```

---

## Verify Persistent Storage

### Check Data is Saved

```bash
# After running conversations, check the database exists
ls -lh ./chroma-data/

# Should show SQLite database files:
# -rw-r--r--  test.db (size depends on data)
```

### Access Stored Memories

```bash
# Query Chroma directly
curl http://localhost:8000/api/v1/collections | jq .

# Should show collections with your memories
```

---

## Memory Verification

### Test 1: Store Memory (First Run)

```bash
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "persistent_test",
    "user_input": "My name is Alice and I work as a data scientist"
  }'

# Check logs:
# [Memory] Extracted durable fact: "User works as a data scientist"
# [Memory] Stored memory: mem_... for session persistent_test
```

### Test 2: Verify Persistence (After App Restart)

```bash
# Stop the backend (Ctrl+C)
# Restart the backend
npm start

# Run same session ID with different query
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "persistent_test",
    "user_input": "What do I do for work?"
  }'

# Expected: Response includes "data scientist"
# This proves Chroma persisted the memory!
```

### Test 3: Verify Data Survives Docker Restart

```bash
# Stop Chroma (Ctrl+C)
# Restart Chroma
docker run -p 8000:8000 -v chroma-data:/chroma/chroma-data chromadb/chroma

# Test memory retrieval again with same session
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "persistent_test",
    "user_input": "What is my job?"
  }'

# Expected: Still recalls "data scientist"
# This proves Docker volume persisted data!
```

---

## Troubleshooting Local Chroma

### Issue: "Cannot reach Chroma: ECONNREFUSED"

**Cause**: Chroma server not running

**Fix**:
```bash
# Terminal 1: Start Chroma
docker run -p 8000:8000 -v chroma-data:/chroma/chroma-data chromadb/chroma

# Terminal 2: Restart backend
npm start
```

### Issue: "Port 8000 already in use"

**Cause**: Chroma already running on port 8000

**Fix**:
```bash
# Find process on port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
docker run -p 8001:8000 -v chroma-data:/chroma/chroma-data chromadb/chroma
# Then set: CHROMA_URL=http://localhost:8001
```

### Issue: Memory not persisting across restarts

**Cause**: Using in-memory storage or wrong volume

**Fix**:
- Use `-v chroma-data:/chroma/chroma-data` flag (volume mount)
- OR use `chroma run --path ./chroma_data` (Python)
- OR use `PersistentClient` in Node.js

### Issue: "Chroma data missing after Docker restart"

**Cause**: Docker volume not mounted correctly

**Fix**:
```bash
# Check volume exists
docker volume ls | grep chroma-data

# If missing, create it
docker volume create chroma-data

# Run with volume
docker run -p 8000:8000 -v chroma-data:/chroma/chroma-data chromadb/chroma
```

---

## Development vs. Production

| Aspect | Development (Local) | Production (Render) |
|--------|-------------------|-------------------|
| **Chroma** | Local SQLite + Docker | Chroma Cloud (hosted) |
| **Database** | `chroma-data/` volume | Cloud-hosted |
| **LLM** | Ollama (local) | Gemini (cloud) |
| **Setup** | `docker run` + `npm start` | render.yaml auto-deploy |
| **Persistence** | Docker volume | Cloud backup |
| **Cost** | $0 | ~$12/month |

---

## Integration with Your Backend

### Current server.js Configuration

Your server.js already supports local Chroma:

```javascript
const CHROMA_URL = process.env.CHROMA_URL || 'http://localhost:8000';
const CHROMA_API_KEY = process.env.CHROMA_API_KEY || null;

let chromaClient;
if (CHROMA_API_KEY) {
  // Production: Chroma Cloud with API key
  chromaClient = new ChromaClient({
    path: CHROMA_URL,
    auth: {
      provider: 'token',
      credentials: CHROMA_API_KEY
    }
  });
} else {
  // Development: Local Chroma server
  chromaClient = new ChromaClient({
    path: CHROMA_URL
  });
}
```

**This means**: Just set `CHROMA_URL=http://localhost:8000` in .env and run local Chroma!

### Update .env for Local Development

```bash
# Copy your .env and modify:
CHROMA_URL=http://localhost:8000
# Don't set CHROMA_API_KEY (leave empty for local)

# Keep other settings:
LLM_PROVIDER=local
OLLAMA_MODEL=qwen2.5:7b-instruct
```

---

## One-Command Setup

### All-in-One Local Development Stack

```bash
# Create docker-compose.yml in project root:
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  chroma:
    image: chromadb/chroma
    ports:
      - "8000:8000"
    volumes:
      - chroma-data:/chroma/chroma-data
    environment:
      - CHROMA_HOST=0.0.0.0
      - CHROMA_PORT=8000

volumes:
  chroma-data:
    driver: local
EOF

# Then start everything:
docker-compose up -d

# Verify:
curl http://localhost:8000/api/v1/heartbeat
# Expected: OK
```

---

## Next Steps

1. **Choose your method**:
   - Docker (recommended): `docker run -p 8000:8000 chromadb/chroma`
   - Python direct: `chroma run --host 0.0.0.0 --port 8000`
   - Node.js persistent: Update server.js

2. **Update .env**:
   ```
   CHROMA_URL=http://localhost:8000
   ```

3. **Test persistence**:
   - Store memory
   - Restart app
   - Verify memory still there

4. **For production**: Switch to Chroma Cloud (see CHROMA_CLOUD_SETUP.md)

---

## References

- Chroma GitHub: https://github.com/chroma-core/chroma
- Chroma Docs: https://docs.trychroma.com
- Docker Hub: https://hub.docker.com/r/chromadb/chroma
- Python Package: https://pypi.org/project/chromadb/
