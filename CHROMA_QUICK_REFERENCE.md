# Chroma Quick Reference Card

## Copy-Paste Commands

### Start Local Chroma (with persistent SQLite)

```bash
docker-compose up -d
```

### Check if Chroma is running

```bash
curl http://localhost:8000/api/v1/heartbeat
# Should return: OK
```

### View Chroma logs

```bash
docker-compose logs -f chroma
```

### Stop Chroma (data stays safe)

```bash
docker-compose down
```

### Stop Chroma and DELETE all data (⚠️ use with caution)

```bash
docker-compose down -v
```

---

## Test Memory Persistence

### Store a memory

```bash
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo",
    "user_input": "My name is Alice and I like Python"
  }'
```

### Retrieve memory (same session)

```bash
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo",
    "user_input": "Who am I?"
  }' | jq '.response_text'

# Expected: Response mentions "Alice"
```

### Verify persistence after restart

```bash
# Stop and restart Chroma
docker-compose down
docker-compose up -d
sleep 5

# Same test - should STILL remember "Alice"
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo",
    "user_input": "What do I like?"
  }' | jq '.response_text'

# Expected: Still mentions "Python" ✅
```

---

## Check Data Files

### List Chroma data directory

```bash
ls -lh chroma-data/
```

### Check volume exists in Docker

```bash
docker volume ls | grep chroma-data
```

---

## Full Development Stack

### Terminal 1: Start Chroma

```bash
docker-compose up -d
```

### Terminal 2: Start Backend

```bash
npm start
```

### Terminal 3: Test API

```bash
curl http://localhost:3000/health | jq .
```

---

## Switch Between Dev & Prod

### Development (.env)

```bash
CHROMA_URL=http://localhost:8000
# No API key needed
```

### Production (.env)

```bash
CHROMA_URL=https://api.trychroma.com
CHROMA_API_KEY=your_key_here
LLM_PROVIDER=gemini
```

---

## Common Issues

| Issue | Fix |
|-------|-----|
| Port 8000 busy | `docker-compose down && docker-compose up -d` |
| Chroma won't start | `docker-compose logs chroma` (check logs) |
| Memory disappeared | Use `down` not `down -v` (don't delete volume!) |
| Can't connect | `curl http://localhost:8000/api/v1/heartbeat` |
| Docker not running | Start Docker Desktop or `sudo service docker start` |

---

## File Locations

```
Project Root/
├── docker-compose.yml              ← Config file
├── chroma-data/                    ← SQLite database (persistent)
├── .env                            ← Your settings
└── server.js                       ← Your backend
```

---

## Your .env Minimal Config

```bash
CHROMA_URL=http://localhost:8000
LLM_PROVIDER=local
OLLAMA_MODEL=qwen2.5:7b-instruct
DEEPGRAM_API_KEY=your_key
```

---

## The One Command

```bash
docker-compose up -d && npm start
```

That's it! You have:
- ✅ Chroma running with SQLite
- ✅ Persistent memory (survives restarts)
- ✅ Backend connected
- ✅ Ready to develop

---

## Read More

- Quick start: `QUICK_LOCAL_CHROMA.md`
- Complete guide: `LOCAL_CHROMA_SETUP.md`
- Production setup: `CHROMA_CLOUD_SETUP.md`
