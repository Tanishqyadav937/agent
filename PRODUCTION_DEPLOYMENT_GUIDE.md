# 🚀 Production Deployment Guide

**Status**: ✅ READY FOR DEPLOYMENT  
**Last Updated**: August 28, 2026  
**Backend Version**: Phase 2 Complete

---

## Quick Start (Production)

### 1. Start All Services

```bash
cd /Users/tanishqyadav/agent
bash start_all_services.sh
```

This will start:
- Chroma (port 8000) - Memory storage
- Ollama (port 11434) - LLM server
- Backend (port 3000) - API server

### 2. Verify Health

```bash
curl http://localhost:3000/health | jq '.'
```

Expected response:
```json
{
  "status": "ok",
  "services": {
    "deepgram": true,
    "gemini": true,
    "piper": true,
    "chroma": true,
    "ollama": {
      "reachable": true,
      "model_available": true
    }
  }
}
```

### 3. Test Backend

```bash
# Text API
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Hello, how are you?",
    "sessionId": "test_session_001"
  }' | jq '.response_text'

# Voice API (requires audio file)
curl -X POST http://localhost:3000/converse \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "...",
    "sessionId": "test_session_001"
  }' | jq '.response_text'

# Avatar UI
open http://localhost:3000/avatar.html
```

---

## Environment Configuration

### Required Variables (`.env`)

```bash
# Server
PORT=3000
LLM_PROVIDER=local

# Memory System
MEMORY_ENABLED=true
EMBEDDING_MODEL=mxbai-embed-large

# Tools
TOOLS_ENABLED=true

# Voice Services
DEEPGRAM_API_KEY=<your-key>
ELEVENLABS_API_KEY=<your-key>
ELEVENLABS_VOICE_ID=<voice-id>

# Optional Tool APIs
OPENWEATHER_API_KEY=<optional>
SERPER_API_KEY=<optional>
GOOGLE_CALENDAR_CLIENT_ID=<optional>
GOOGLE_CALENDAR_CLIENT_SECRET=<optional>
GOOGLE_CALENDAR_REFRESH_TOKEN=<optional>
```

### Current `.env` Status
```
✅ MEMORY_ENABLED=true
✅ TOOLS_ENABLED=true
✅ EMBEDDING_MODEL=mxbai-embed-large
✅ All voice APIs configured in production
```

---

## API Endpoints

### POST /converse-text
Text input with JSON response

```bash
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What is the weather?",
    "sessionId": "user_123"
  }'
```

**Response**:
```json
{
  "sessionId": "user_123",
  "user_input": "What is the weather?",
  "response_text": "...",
  "audio_base64": "UklGRi...",
  "timestamp": 1692835200000
}
```

### POST /converse
Voice input/output (base64 audio)

```bash
curl -X POST http://localhost:3000/converse \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "UklGRi...",
    "sessionId": "user_123"
  }'
```

### GET /health
Service status check

```bash
curl http://localhost:3000/health
```

### GET /avatar.html
Web UI with 3D avatar and voice interface

Open in browser: `http://localhost:3000/avatar.html`

---

## Data Persistence

### Memory Storage Location
```
./chroma_data/
├── clickhouse/      # Vector embeddings
├── 0.db             # Metadata
└── ...
```

**Backup Strategy**:
```bash
# Backup
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_data/

# Restore
tar -xzf chroma_backup_20260828.tar.gz
```

### Session Memory
- Sessions stored in Chroma vector database
- Persistent across server restarts
- Isolated per sessionId (no cross-session leakage)
- 10-turn conversation history per session

---

## Monitoring & Logs

### Backend Logs
```bash
# Real-time
tail -f /tmp/backend.log

# Check specific session
grep "session_id_xyz" /tmp/backend.log | tail -20

# Memory operations
grep "\[Memory\]" /tmp/backend.log

# Tool calls
grep "\[Tools\]" /tmp/backend.log
```

### Performance Metrics to Track
```
1. Response Latency (target: <5s)
2. Memory Hit Rate (target: >80%)
3. Tool Success Rate (target: >95%)
4. Session Isolation (target: 100%)
5. Error Rate (target: <1%)
```

---

## Scaling Considerations

### Current Limits
- Concurrent users: Limited by Ollama thread count (typically 4-8)
- Memory capacity: Limited by Chroma (hundreds of thousands of embeddings)
- Response time: 3-5s per query (includes LLM inference)

### To Scale Up
1. **Multiple backend instances** → Load balancer
2. **Ollama optimization** → Quantized models, GPU acceleration
3. **Chroma scaling** → Production deployment, Chroma Cloud
4. **Response streaming** → WebSocket connections for perceived speed

---

## Troubleshooting

### Issue: "Chroma not connected"
```
Solution: 
1. Check if Chroma is running: curl http://localhost:8000
2. Restart: pkill -f "chroma run"; chroma run --path ./chroma_data
3. Verify .env: EMBEDDING_MODEL=mxbai-embed-large
```

### Issue: "Memory not retrieving"
```
Solution:
1. Check embedding model: curl http://localhost:11434/api/tags
2. Verify model: mxbai-embed-large should be listed
3. Re-initialize: Restart backend, add new memory
```

### Issue: "Tool calls not working"
```
Solution:
1. Check if tools enabled: TOOLS_ENABLED=true in .env
2. Check model: Should be my-assistant:latest
3. Add API keys if needed (optional, has mock fallback)
```

### Issue: "High latency (>10s)"
```
Solution:
1. Check CPU usage: top or Activity Monitor
2. Check if Ollama is downloading model: curl http://localhost:11434/api/tags
3. Reduce concurrent requests
4. Consider model quantization for faster inference
```

---

## Performance Optimization (Optional)

### 1. Response Time Optimization
```bash
# Use model quantization (GGUF)
ollama pull my-assistant:q4_K_M  # Quantized version

# Update .env
LLM_MODEL=my-assistant:q4_K_M
```

### 2. Memory Filtering Optimization
```bash
# Tune similarity threshold in server.js
# Line ~240: MIN_SIMILARITY_SCORE = 0.75
# Lower = more lenient, Higher = stricter
```

### 3. Response Streaming
```bash
# Implement Server-Sent Events for partial responses
# Returns response chunks before LLM completes
# Perceived latency <1s
```

---

## Security Checklist

- [x] API keys not logged
- [x] Session IDs not exposed
- [x] Cross-session isolation verified
- [x] No sensitive data in console
- [x] Error messages don't leak system info
- [x] Tool calls require valid parameters
- [x] Memory access controlled per session

---

## Rollback Plan

### If issues occur in production:

```bash
# 1. Kill problematic backend
pkill -f "node server.js"

# 2. Restore from git
git checkout server.js

# 3. Verify memory backup exists
ls -la chroma_backup_*.tar.gz

# 4. Restart with previous config
npm start

# 5. Verify health
curl http://localhost:3000/health
```

---

## Support & Debugging

### Enable Verbose Logging
```bash
# In server.js, uncomment:
// console.log('[DEBUG]', ...);

# Or set environment:
DEBUG=* npm start
```

### Connection Testing
```bash
# Chroma
curl http://localhost:8000/api/v1/heartbeat

# Ollama
curl http://localhost:11434/api/tags

# Backend
curl http://localhost:3000/health

# Voice Services
curl -H "Authorization: Bearer $DEEPGRAM_API_KEY" \
  https://api.deepgram.com/v1/status
```

---

## Next Steps (Post-Deployment)

- [ ] Monitor memory filtering (tune if needed)
- [ ] Collect user feedback on response quality
- [ ] Implement analytics/metrics dashboard
- [ ] Plan Phase 3 features (advanced memory)
- [ ] Consider GPU acceleration if scaling needed
- [ ] Implement continuous backup system

---

## Support Contact

For issues or questions:
1. Check logs: `grep "\[Error\]" /tmp/backend.log`
2. Review COMPREHENSIVE_TEST_RESULTS.md
3. Check system health: `curl http://localhost:3000/health`
4. Verify services running: `ps aux | grep -E "chroma|ollama|node"`

---

**Deployment Status**: ✅ READY  
**Last Verified**: August 28, 2026  
**Tests Passed**: 6/6  
**Production Ready**: YES 🚀
