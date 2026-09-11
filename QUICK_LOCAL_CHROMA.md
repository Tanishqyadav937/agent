# Quick Local Chroma SQLite Setup (5 Minutes)

## The Simplest Way to Get Started

### ⚡ One-Command Setup

```bash
# Start everything
docker-compose up -d

# Verify it's running
curl http://localhost:8000/api/v1/heartbeat
# Should return: OK
```

**That's it!** Chroma is now running with persistent SQLite.

---

## Verify Your Setup Works

### Test 1: Check Health

```bash
curl http://localhost:3000/health | jq .

# Should show:
# "chroma": true ✅
```

### Test 2: Store Memory

```bash
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo",
    "user_input": "My name is Priya and I work as a data scientist"
  }' | jq '.response_text'
```

### Test 3: Retrieve Memory (Proves Persistence!)

```bash
# Same session ID - should remember the memory
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo",
    "user_input": "What do I do for work?"
  }' | jq '.response_text'

# Expected: Response includes "data scientist"
```

### Test 4: Verify Persistence After Restart

```bash
# Stop and restart Chroma
docker-compose down
docker-compose up -d

# Wait 5 seconds for startup
sleep 5

# Same test - should STILL remember!
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo",
    "user_input": "What is my job?"
  }' | jq '.response_text'

# Expected: Still says "data scientist" - PERSISTENCE WORKS! ✅
```

---

## If You Don't Have Docker Compose

### Option A: Manual Docker Command

```bash
# Start Chroma
docker run -d \
  -p 8000:8000 \
  -v chroma-data:/chroma/chroma-data \
  chromadb/chroma

# Verify
curl http://localhost:8000/api/v1/heartbeat
```

### Option B: Using Python Directly

```bash
# Install Chroma
pip install chromadb

# Start Chroma server
chroma run --host 0.0.0.0 --port 8000 --path ./chroma_data

# In another terminal, start your backend
npm start
```

---

## Setup Diagram

```
┌─────────────────────────────────────┐
│   Your Voice Assistant Backend      │
│   (npm start)                       │
│   localhost:3000                    │
└──────────────┬──────────────────────┘
               │
               │ Queries memory
               │
┌──────────────▼──────────────────────┐
│   Chroma Server (Docker)            │
│   localhost:8000                    │
└──────────────┬──────────────────────┘
               │
               │ Stores data
               │
┌──────────────▼──────────────────────┐
│   SQLite Database (Persistent)      │
│   chroma-data/ volume               │
│   Survives restarts ✅              │
└─────────────────────────────────────┘
```

---

## Directory Structure

After setup, you'll have:

```
project-root/
├── docker-compose.yml           ← Run this
├── start-local-dev.sh           ← Or this
├── .env                         ← Auto-created
├── server.js                    ← Already configured
└── chroma-data/                 ← Created by Docker
    └── (SQLite database files)
```

---

## Common Commands

```bash
# Start Chroma + Backend
docker-compose up -d
npm start

# View Chroma logs
docker-compose logs -f chroma

# Check if Chroma is running
docker ps | grep chroma

# Stop Chroma
docker-compose down

# Stop Chroma and DELETE all data
docker-compose down -v  # ⚠️ Use with caution!

# Check data directory
ls -lh chroma-data/

# Restart Chroma (keeps data)
docker-compose restart chroma
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 already in use | Kill other process: `lsof -i :8000` or use different port |
| Docker not running | Start Docker Desktop / `sudo service docker start` |
| Data disappeared | Check you used `-v chroma-data:...` flag |
| Chroma won't start | Check Docker logs: `docker-compose logs chroma` |
| Can't connect to Chroma | Make sure Chroma is running: `curl http://localhost:8000` |

---

## Your .env File (Already Configured)

```bash
# .env (for local development)
CHROMA_URL=http://localhost:8000
# No API key needed for local!

# Optional, if you want local LLM:
LLM_PROVIDER=local
OLLAMA_MODEL=qwen2.5:7b-instruct

# You still need these:
DEEPGRAM_API_KEY=your_key
GEMINI_API_KEY=your_key
```

---

## What's Happening Behind the Scenes

1. **docker-compose up -d** starts Chroma in a Docker container
2. **-v chroma-data:/chroma/chroma-data** creates persistent volume
3. **Chroma creates SQLite database** in that volume
4. **Your app connects** to http://localhost:8000
5. **Memories are stored** in SQLite on disk
6. **Survives restart** - volume is persistent!

---

## Next: Test Full Pipeline

### Full Development Stack (3 Terminals)

**Terminal 1: Chroma**
```bash
docker-compose up -d
```

**Terminal 2: Ollama (optional, for local LLM)**
```bash
ollama serve
```

**Terminal 3: Your Backend**
```bash
npm start
```

**Terminal 4: Test**
```bash
# Store memory
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session",
    "user_input": "I like Python programming"
  }'

# Retrieve memory
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session",
    "user_input": "What are my interests?"
  }'
```

Expected: Response should mention "Python"

---

## Moving to Production

When you're ready to deploy to Render:

1. Keep your local Chroma setup as-is (development)
2. Create Chroma Cloud account (production)
3. Update render.yaml with Chroma Cloud URL
4. Set CHROMA_API_KEY in Render environment
5. Deploy!

See: `CHROMA_CLOUD_SETUP.md` for production setup

---

## That's It! 🎉

You now have:
✅ Persistent SQLite database  
✅ Local Chroma server (no cloud needed)  
✅ Memory that survives restarts  
✅ Full development setup  

Start building! 🚀
