# Quick Start - Client ↔ Backend Integration

## 🚀 Run Everything Locally (5 minutes)

### Terminal 1: Backend

```bash
cd /Users/tanishqyadav/agent

# Install dependencies (if needed)
npm install --legacy-peer-deps

# Start backend
npm start

# Expected output:
# ✓ Server running on http://localhost:3000
# ✓ /health endpoint ready
```

### Terminal 2: Frontend

```bash
cd /Users/tanishqyadav/agent/bunny-buddy-client

# Install dependencies (if needed)
npm install

# Start dev server
npm run dev

# Expected output:
# ✓ Local: http://localhost:5173/
```

### Terminal 3: Services (Optional - for local LLM)

```bash
# Start Chroma + Ollama (if using local LLM)
cd /Users/tanishqyadav/agent

docker-compose up -d

# Verify:
# ✓ http://localhost:8000 - Chroma
# ✓ http://localhost:11434 - Ollama
```

---

## 🔗 Connection Flow (Slow, Step-by-Step)

```
┌─ USER CLICKS "BUNNY BUDDY ORB" ─┐
│                                  │
│  Frontend (React)                │
│  useBunnyVoiceSession()          │
│  startTurn()                     │
│  ├─ Request microphone           │
│  ├─ Create MediaRecorder         │
│  └─ Ready for audio              │
│                                  │
└─ USER SPEAKS "HELLO" ────────────┘

┌─ USER CLICKS ORB AGAIN ──────────┐
│                                  │
│  Frontend                        │
│  stopTurn()                      │
│  ├─ Stop recording               │
│  ├─ Create blob (webm audio)     │
│  └─ converseWithAudio(blob)      │
│                                  │
├─ HTTP POST /converse ────────────┤
│  multipart/form-data             │
│  ├─ audio: [blob]                │
│  ├─ sessionId: (optional)        │
│                                  │
├─ NETWORK ────────────────────────┤
│  sends blob → backend            │
│                                  │
│  Backend Processing:             │
│  ├─ Extract audio                │
│  ├─ Deepgram STT → "hello"       │
│  ├─ Generate embedding           │
│  ├─ Query Chroma memory          │
│  ├─ Build LLM prompt             │
│  ├─ Call Gemini/Ollama           │
│  ├─ Generate TTS audio           │
│  ├─ Return WAV                   │
│                                  │
├─ HTTP RESPONSE ───────────────────┤
│  200 OK                          │
│  audio/wav + X-Session-ID        │
│                                  │
├─ NETWORK ────────────────────────┤
│  returns audio → frontend        │
│                                  │
│  Frontend                        │
│  playResponse(audio)             │
│  ├─ Create Audio element         │
│  ├─ Connect to AnalyserNode      │
│  ├─ Play audio                   │
│  ├─ Show "speaking" orb          │
│  └─ Ready for next turn          │
│                                  │
└─ USER HEARS "HI THERE!" ─────────┘
```

---

## 📡 API Endpoints

### POST /converse (Main)
```bash
# Send audio, get audio back

curl -X POST http://localhost:3000/converse \
  -F "audio=@recording.webm" \
  -F "sessionId=user-123"

# Response:
# - Header: X-Session-ID: user-123
# - Body: audio/wav binary data
```

### POST /converse-text (Text Fallback)
```bash
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","sessionId":"user-123"}'

# Response:
# - Header: X-Session-ID: user-123
# - Body: audio/wav binary data
```

### GET /health (Status Check)
```bash
curl http://localhost:3000/health

# Response:
# {
#   "status": "healthy",
#   "services": {
#     "deepgram": true,
#     "gemini": true,
#     "piper": true,
#     "chroma": true
#   }
# }
```

---

## 🎯 Key Files

### Frontend (`bunny-buddy-client/`)

| File | Purpose |
|---|---|
| `src/App.tsx` | Main UI component |
| `src/components/voice-orb.tsx` | WebGL animated orb |
| `src/components/voice-control.tsx` | Control buttons |
| `src/hooks/use-bunny-voice-session.ts` | ALL state management |
| `src/lib/bunny-api.ts` | API client (fetch wrapper) |

### Backend (`/`)

| File | Purpose |
|---|---|
| `server.js` | Express app + routes |
| `tools.js` | Tool definitions |
| `.env` | API keys (Deepgram, Gemini, etc.) |
| `Dockerfile` | Production container |
| `render.yaml` | Render.com deployment |

---

## 🔄 Session ID Management

```
First interaction:
  Client: sends null (no sessionId yet)
  Backend: generates "session_abc123"
  Backend: returns X-Session-ID header
  Client: stores in sessionIdRef.current

Subsequent interactions (SAME SESSION):
  Client: sends with sessionId = "session_abc123"
  Backend: uses same session buffer
  Backend: queries memory by sessionId
  Backend: returns same sessionId

Benefits:
  ✓ Maintains last 10 turns in-memory
  ✓ Retrieves persistent memories
  ✓ Session isolation (no data leaks)
```

---

## 🧠 Memory System

```
DURABLE MEMORY FLOW:

User says: "I prefer dark mode"
    ↓
Backend extracts: "User prefers dark mode"
    ↓
Generate embedding: [0.12, 0.45, 0.78, ...]
    ↓
Store in Chroma:
  ├─ text: "User prefers dark mode"
  ├─ embedding: [vector]
  ├─ sessionId: "session_abc123"
  └─ metadata: { timestamp: "..." }
    ↓
LATER: User asks "What do I prefer?"
    ↓
Query Chroma: similarity search
    ↓
Find match: "User prefers dark mode" (distance 0.35)
    ↓
Inject into LLM prompt:
  "RELEVANT MEMORIES:
   - User prefers dark mode"
    ↓
LLM response: "You mentioned dark mode!"
```

---

## ⚙️ Configuration Files

### Frontend: bunny-buddy-client/.env
```env
# Backend URL (auto-detects localhost for dev)
VITE_BUNNY_API_URL=http://localhost:3000
```

### Backend: .env
```env
# Required API Keys
DEEPGRAM_API_KEY=your_deepgram_key
GEMINI_API_KEY=your_gemini_key

# LLM Provider
LLM_PROVIDER=local        # dev: local (Ollama)
                          # prod: gemini

# Memory
CHROMA_URL=http://localhost:8000

# Server
PORT=3000
NODE_ENV=development
```

---

## 🧪 Testing the Connection

### Test 1: Backend is running
```bash
curl http://localhost:3000/health
# Should return JSON with "status": "healthy"
```

### Test 2: Frontend can reach backend
```bash
# In browser console:
fetch('http://localhost:3000/health')
  .then(r => r.json())
  .then(console.log)
# Should print health status
```

### Test 3: Full round trip (with audio file)
```bash
# Record audio locally or use test file
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" \
  --output response.wav

# Play response
afplay response.wav  # macOS
```

---

## 🚨 Common Problems & Quick Fixes

| Problem | Fix |
|---|---|
| "Couldn't reach Bunny Buddy" | Start backend: `npm start` |
| CORS error | Backend running? Check `app.use(cors(...))` |
| Microphone permission denied | Grant permission in browser settings |
| "Deepgram error" | Check DEEPGRAM_API_KEY in .env |
| No audio reply | Check Piper TTS: `ls piper-venv/bin/piper` |
| Backend crashes | Check .env file has all required keys |

---

## 📊 Performance

```
Microphone recording:     ~2 seconds (user)
Send to backend:          <1 second (network)
Deepgram STT:             1-3 seconds (API)
Embedding + Memory:       ~1 second (local)
LLM inference:            2-5 seconds (API) ← MAIN BOTTLENECK
Piper TTS:                1-2 seconds (local)
─────────────────────────────────────────
Total:                    ~7-14 seconds
```

---

## 🎮 User Experience

```
1. Click "Connect" → Browser asks for microphone
2. Tap Bunny Buddy orb → Starts recording (orb glows)
3. Speak into microphone → Orb reacts to voice volume
4. Tap orb again → Sends to backend
5. Wait ~7-14 seconds → Backend processes
6. Orb animates → Bunny Buddy speaks response
7. Response plays → Audio plays through speakers
8. Tap orb → Ready for next message
```

---

## 📚 Full Documentation

For deep dives, see:

- `CLIENT_BACKEND_INTEGRATION.md` - Full 992-line analysis
- `ARCHITECTURE.md` - System design & scalability
- `PROJECT_DESCRIPTION.md` - Project overview
- `README.md` - Basic setup

---

## ✅ Next Steps

1. ✅ Backend running: `npm start` (port 3000)
2. ✅ Frontend running: `npm run dev` (port 5173)
3. ✅ Open browser: http://localhost:5173
4. ✅ Click "Connect"
5. ✅ Tap Bunny Buddy orb
6. ✅ Speak
7. ✅ Tap again
8. ✅ Hear response!

---

**Status**: Ready to Run ✅  
**Version**: 1.0  
**Last Updated**: August 28, 2026
