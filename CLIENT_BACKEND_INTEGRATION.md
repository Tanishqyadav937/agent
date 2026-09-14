# Bunny Buddy Client ↔ Backend Integration Analysis

## 📋 Overview

This document provides a **detailed slow analysis** of how the React frontend client connects to and communicates with the Node.js backend server.

---

## 🏗️ System Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    REACT CLIENT                                 │
│              (bunny-buddy-client/)                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ App.tsx (Main Component)                                 │  │
│  │ └─ Renders VoiceOrb + VoiceControl UI                   │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │                                               │
│                 ▼                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ useBunnyVoiceSession() (React Hook)                      │  │
│  │                                                          │  │
│  │ State Management:                                        │  │
│  │ ├─ status: idle | connecting | running | ended          │  │
│  │ ├─ isMuted: boolean                                      │  │
│  │ ├─ mode: listening | speaking                           │  │
│  │ ├─ isRecording: boolean                                  │  │
│  │ ├─ level: 0-1 (volume meter)                            │  │
│  │ ├─ turns: VoiceTurn[] (conversation history)            │  │
│  │ └─ error: string | null                                 │  │
│  │                                                          │  │
│  │ Actions:                                                │  │
│  │ ├─ connect() → Request microphone                        │  │
│  │ ├─ disconnect() → Stop recording + cleanup              │  │
│  │ ├─ toggleMute() → Mute/unmute microphone               │  │
│  │ └─ toggleTurn() → Start/stop recording → Send to API   │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │                                               │
│                 ▼                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ bunny-api.ts (API Client)                                │  │
│  │                                                          │  │
│  │ Functions:                                              │  │
│  │ ├─ converseWithAudio(blob, sessionId)                   │  │
│  │ │  Sends: multipart/form-data                           │  │
│  │ │  Receives: audio/wav + X-Session-ID header            │  │
│  │ │                                                       │  │
│  │ ├─ converseWithText(text, sessionId)                    │  │
│  │ │  Sends: application/json                              │  │
│  │ │  Receives: audio/wav + X-Session-ID header            │  │
│  │ │                                                       │  │
│  │ └─ checkHealth()                                        │  │
│  │    Checks: GET /health endpoint                        │  │
│  │                                                          │  │
│  │ Base URL: process.env.VITE_BUNNY_API_URL ??             │  │
│  │           "http://localhost:3000"                       │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │                                               │
└─────────────────┼───────────────────────────────────────────────┘
                  │
                  │ HTTP/REST API
                  │
        ┌─────────▼──────────┐
        │  HTTP Requests     │
        │  (multipart/json)  │
        └─────────┬──────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                  NODE.JS BACKEND                                │
│                (server.js)                                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Express Routes                                           │  │
│  │                                                          │  │
│  │ POST /converse                                          │  │
│  │ ├─ Input: multipart/form-data                           │  │
│  │ │  Fields: audio (blob), sessionId (optional)           │  │
│  │ ├─ Processing:                                          │  │
│  │ │  1. Extract audio + sessionId                         │  │
│  │ │  2. Call transcribeAudio() → Deepgram STT             │  │
│  │ │  3. Call generateEmbedding() → Xenova embeddings      │  │
│  │ │  4. Call retrieveRelevantMemories() → Chroma query    │  │
│  │ │  5. Build augmented prompt                            │  │
│  │ │  6. Call getLLMResponseWithContext() → Gemini/Ollama  │  │
│  │ │  7. Extract memory (background) → async              │  │
│  │ │  8. Call textToSpeech() → Piper TTS                   │  │
│  │ │  9. Update session buffer                             │  │
│  │ └─ Output: audio/wav + X-Session-ID header              │  │
│  │                                                          │  │
│  │ POST /converse-text                                     │  │
│  │ ├─ Input: application/json                              │  │
│  │ │  Body: { message, sessionId? }                        │  │
│  │ ├─ Processing: Same as /converse (skip STT)             │  │
│  │ └─ Output: audio/wav + X-Session-ID header              │  │
│  │                                                          │  │
│  │ GET /health                                             │  │
│  │ ├─ Input: None                                          │  │
│  │ ├─ Processing: Check all services                       │  │
│  │ └─ Output: JSON status                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request/Response Flow - Detailed Breakdown

### Flow 1: User Records Audio & Sends to Backend

```
STEP 1: User Taps "Bunny Buddy" Orb
   │
   └─→ App.tsx calls toggleTurn()
        │
        └─→ useBunnyVoiceSession.toggleTurn()
             ├─ isRecording = false initially
             ├─ Call startTurn()
             │
             └─→ startTurn()
                  ├─ Create AudioContext
                  ├─ Create AnalyserNode (for volume meter)
                  ├─ Create MediaRecorder from microphone stream
                  ├─ Set up event handlers:
                  │  ├─ ondataavailable: collect audio chunks
                  │  └─ onstop: prepare audio blob
                  ├─ recorder.start()
                  └─ setIsRecording(true)

             Status: "running" | isRecording: true
             User hears: "Listening — tap the orb to send"
             VoiceOrb: Shows "listening" state


STEP 2: User Speaks Into Microphone
   │
   └─→ MediaRecorder captures audio from microphone stream
        │
        ├─ Analyser continuously samples audio
        │ └─→ useLevelMeter() updates volume (0-1)
        │    └─→ VoiceOrb visualizes volume changes
        │
        └─→ User sees: Orb reacting to voice


STEP 3: User Taps Orb Again to Send
   │
   └─→ App.tsx calls toggleTurn()
        │
        └─→ useBunnyVoiceSession.toggleTurn()
             ├─ isRecording = true now
             ├─ Call stopTurn()
             │
             └─→ stopTurn()
                  ├─ recorder.stop()
                  ├─ Triggers recorder.onstop event
                  │
                  └─→ onstop handler:
                       ├─ Create Blob from chunks
                       ├─ Add to turns history: "Voice message"
                       ├─ setStatus("connecting")
                       ├─ Call API:
                       │
                       └─→ converseWithAudio(blob, sessionIdRef.current)
```

### Flow 2: Frontend Sends Audio to Backend API

```
converseWithAudio(audioBlob, sessionId) in bunny-api.ts:
   │
   ├─ Create FormData
   │  ├─ form.append("audio", audioBlob, "utterance.webm")
   │  └─ form.append("sessionId", sessionId)  [if exists]
   │
   ├─ fetch("http://localhost:3000/converse", {
   │   method: "POST",
   │   body: form,
   │   headers: { "X-Session-ID": sessionId } [if exists]
   │ })
   │
   └─→ Network Request Sent
       Content-Type: multipart/form-data
       Payload:
       ├─ audio: WebM audio blob
       └─ sessionId: string (optional)
```

### Flow 3: Backend Processes Audio

```
Express Server (server.js) receives POST /converse:
   │
   └─→ app.post('/converse', upload.single('audio'), async (req, res) => {

       STEP 1: VALIDATE INPUT
       │ ├─ Extract audio from req.files.audio
       │ ├─ Extract sessionId from req.body or req.headers['X-Session-ID']
       │ ├─ Validate audio size + format
       │ └─ Handle errors (400 Bad Request)
       │
       STEP 2: SPEECH-TO-TEXT (STT)
       │ └─→ transcribeAudio(audioBuffer)
       │     ├─ Send to Deepgram API: /v1/listen
       │     ├─ Deepgram processes audio
       │     └─ Return transcript: "Hello Bunny"
       │
       STEP 3: GENERATE EMBEDDING
       │ └─→ generateEmbedding(transcript)
       │     ├─ Load Xenova/all-MiniLM-L6-v2 (first time only)
       │     ├─ Convert text to 384-dim vector
       │     └─ Return: [0.12, 0.45, ...]
       │
       STEP 4: MEMORY RETRIEVAL
       │ └─→ retrieveRelevantMemories(sessionId, transcript)
       │     ├─ Query Chroma vector store
       │     ├─ Find top-3 similar memories
       │     ├─ Apply threshold filter (< 0.95)
       │     └─ Return: ["User prefers dark mode", ...]
       │
       STEP 5: BUILD CONTEXT PROMPT
       │ └─→ buildContextPrompt(sessionId, transcript, memories)
       │     └─ Combine:
       │        ├─ SYSTEM_PROMPT (character definition)
       │        ├─ RELEVANT_MEMORIES (retrieved facts)
       │        ├─ RECENT_CONVERSATION (last 10 turns)
       │        └─ CURRENT_MESSAGE (user transcript)
       │
       STEP 6: LLM INFERENCE (Parallel to memory extraction)
       │ └─→ getLLMResponseWithContext(contextPrompt)
       │     ├─ Check LLM_PROVIDER env var:
       │     │  ├─ "gemini" → Call Google Gemini API
       │     │  └─ "local" → Call Ollama localhost:11434
       │     ├─ Send prompt with context
       │     └─ Return: "Hey there! I'm Bunny Buddy..."
       │
       STEP 7: ASYNC MEMORY EXTRACTION (Non-blocking)
       │ └─→ extractDurableMemory(transcript)
       │     ├─ Analyze: "Hello Bunny" → Not durable fact
       │     └─ Return: null (nothing to store)
       │     [If user said "I prefer dark mode":
       │      └─→ Extract "User prefers dark mode"
       │          └─→ Store in Chroma (async)]
       │
       STEP 8: TEXT-TO-SPEECH (TTS)
       │ └─→ textToSpeech(llmResponse)
       │     ├─ Call Piper TTS via subprocess
       │     ├─ Use voice model: en_US-lessac-medium.onnx
       │     ├─ Generate WAV audio file
       │     └─ Return: ArrayBuffer (WAV data)
       │
       STEP 9: UPDATE SESSION BUFFER
       │ └─→ addTurnToSession(sessionId, transcript, llmResponse)
       │     ├─ Store: { user: transcript, assistant: response }
       │     ├─ Keep only last 10 turns
       │     └─ Ready for next interaction
       │
       └─→ Send Response:
           ├─ Content-Type: audio/wav
           ├─ Body: WAV audio buffer
           ├─ Header: X-Session-ID (for future turns)
           └─ Status: 200 OK
   })
```

### Flow 4: Frontend Receives Audio Response

```
unwrapAudioResponse(res) in bunny-api.ts:
   │
   ├─ Check: res.ok === true?
   │  └─ If false: throw error with status + message
   │
   ├─ Extract audio blob: await res.blob()
   │  └─ Blob of audio/wav data
   │
   ├─ Extract session ID: res.headers.get('X-Session-ID')
   │  └─ String or null
   │
   └─→ Return: { audio: Blob, sessionId: string | null }


useBunnyVoiceSession.onstop handler continues:
   │
   ├─ Receive response:
   │  ├─ audio (WAV blob)
   │  └─ sessionId (to reuse for future turns)
   │
   ├─ Store sessionId: sessionIdRef.current = sessionId
   │
   ├─ Add to turns: { role: "assistant", label: "Reply" }
   │
   ├─ setStatus("running")
   │
   ├─ Call playResponse(audio):
   │  │
   │  └─→ playResponse():
   │      ├─ Create AudioContext
   │      ├─ Create Audio element from blob
   │      ├─ Connect to AnalyserNode (for volume visualization)
   │      ├─ setMode("speaking")
   │      ├─ audio.play()
   │      │
   │      ├─ Orb shows "speaking" state
   │      ├─ Orb visualizes volume in real-time
   │      │
   │      └─ When audio.onended:
   │          ├─ attach(null) — stop analyser
   │          ├─ setMode("listening")
   │          └─ Ready for next turn
   │
   └─→ Back to IDLE state
```

---

## 📡 Network Communication Protocols

### HTTP POST /converse (Audio)

**Request:**
```
POST http://localhost:3000/converse HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
X-Session-ID: session_abc123  (optional header)

------WebKitFormBoundary...
Content-Disposition: form-data; name="audio"; filename="utterance.webm"
Content-Type: audio/webm

[Binary audio data]
------WebKitFormBoundary...
Content-Disposition: form-data; name="sessionId"

session_abc123
------WebKitFormBoundary...--
```

**Response:**
```
HTTP/1.1 200 OK
Content-Type: audio/wav
X-Session-ID: session_abc123

[Binary WAV audio data]
```

### HTTP POST /converse-text (Text)

**Request:**
```
POST http://localhost:3000/converse-text HTTP/1.1
Content-Type: application/json
X-Session-ID: session_abc123  (optional header)

{
  "message": "Hello Bunny Buddy",
  "sessionId": "session_abc123"
}
```

**Response:**
```
HTTP/1.1 200 OK
Content-Type: audio/wav
X-Session-ID: session_abc123

[Binary WAV audio data]
```

### HTTP GET /health

**Request:**
```
GET http://localhost:3000/health HTTP/1.1
```

**Response:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "services": {
    "deepgram": true,
    "gemini": true,
    "piper": true,
    "chroma": true,
    "ollama": {
      "reachable": true,
      "model_available": true,
      "model_name": "llama3.2"
    }
  }
}
```

---

## 🎣 Session Management

### Session ID Flow

```
FIRST INTERACTION:
   │
   ├─ Client: No sessionId stored (sessionIdRef.current = null)
   │
   ├─ Client sends: converseWithAudio(blob, null)
   │  └─ No X-Session-ID header
   │
   ├─ Server: Generates new sessionId (e.g., "session_xyz789")
   │
   └─ Server sends: X-Session-ID: session_xyz789 in response


SUBSEQUENT INTERACTIONS (SAME SESSION):
   │
   ├─ Client: Store sessionId from previous response
   │  └─ sessionIdRef.current = "session_xyz789"
   │
   ├─ Client sends: converseWithAudio(blob, "session_xyz789")
   │  └─ Includes X-Session-ID header + form field
   │
   ├─ Server: Receives sessionId
   │  ├─ Retrieves session buffer (last 10 turns)
   │  ├─ Uses same sessionId for memory queries
   │  └─ Returns same sessionId in response
   │
   └─ Client: Stores sessionId (already has it)


CONVERSATION MEMORY:
   │
   ├─ Per-Session Buffer (In-Memory):
   │  ├─ Stores: Last 10 turns
   │  ├─ Lives: Duration of session
   │  ├─ Lost: On server restart
   │  └─ Access: O(1) lookup
   │
   └─ Persistent Memory (Chroma):
       ├─ Stores: Durable facts
       ├─ Indexed: By sessionId + embedding
       ├─ Lives: Indefinite
       ├─ Access: O(log n) similarity search
       └─ Example: "User prefers dark mode"
```

---

## 🎯 Frontend Components - Detailed Breakdown

### VoiceControl.tsx

```typescript
// Purpose: Status bar + action buttons

Props:
├─ status: "idle" | "connecting" | "running" | "ended"
│  └─ Controls visibility of buttons
│
├─ isMuted: boolean
│  └─ Shows mute/unmute button when running
│
├─ onConnect: () => void
│  └─ User clicks "Connect" button
│  └─ Requests microphone permission
│
├─ onDisconnect: () => void
│  └─ User clicks red phone icon
│  └─ Stops recording + cleanup
│
└─ onToggleMute: () => void
   └─ User clicks mic/mic-off icon
   └─ Toggles microphone enabled/disabled

Visual States:
├─ Idle: "Connect" button + status dot (white/25)
├─ Connecting: Spinner + "Connecting…" text + pulse dot (amber)
└─ Running: Mute + Disconnect buttons + solid dot (green)
```

### VoiceOrb.tsx

```typescript
// Purpose: Animated WebGL2 orb visualization

States:
├─ "idle": Slow, dim animation (status: not connected)
├─ "connecting": Fast pulse with glow (status: connecting)
├─ "listening": Medium speed, reactive (user can talk)
├─ "speaking": Fast, bright, volume-reactive (Bunny replying)
└─ "muted": Very dim, barely animated (microphone muted)

Animations (WebGL Shaders):
├─ Simplex noise (3D Perlin noise)
│  └─ Creates organic, flowing surface
├─ Distortion waves
│  └─ Amplitude linked to volume
├─ Color shifting
│  └─ Blends between 3 color channels
├─ Specular highlights
│  └─ Fake glossy surface
└─ Pulsing effect
   └─ Optional for certain states

Volume Reactivity:
├─ When recording: Analyser samples microphone
│  └─ Updates orb amplitude in real-time
├─ When playing: Analyser samples audio playback
│  └─ Orb reacts to assistant's voice
└─ Smooth easing (0.6 decay) for natural motion

Variant Colors:
├─ "default": Gray tones
├─ "blue": Blue tones
├─ "violet": Purple tones (used in App.tsx)
└─ "emerald": Green tones
```

### useBunnyVoiceSession() Hook

```typescript
// Purpose: All state management + audio handling

State:
├─ status: VoiceSessionStatus
│  └─ Drives UI visibility + buttons
├─ isMuted: boolean
│  └─ Mute button state
├─ mode: "listening" | "speaking"
│  └─ Determines orb animation
├─ isRecording: boolean
│  └─ Is MediaRecorder active?
├─ level: 0-1
│  └─ RMS volume for visualization
├─ turns: VoiceTurn[]
│  └─ Conversation history (last 4 shown)
└─ error: string | null
   └─ Error messages displayed to user

Refs (Persistent):
├─ sessionIdRef: current session ID
├─ audioCtxRef: shared AudioContext
├─ streamRef: MediaStream from microphone
├─ recorderRef: MediaRecorder instance
├─ chunksRef: collected audio chunks
└─ playbackElRef: Audio element for playback

Key Functions:
├─ connect(): Request microphone permission
├─ disconnect(): Stop + cleanup
├─ toggleMute(): Mute/unmute mic
├─ startTurn(): Create MediaRecorder
├─ stopTurn(): Stop recording
├─ toggleTurn(): Start or stop recording
├─ playResponse(): Play audio blob
└─ useLevelMeter(): Volume tracking

Flow:
   User connects
   └─→ Get microphone stream
       └─→ Stream stays in streamRef
           └─→ User taps orb to start recording
               └─→ Create MediaRecorder from stream
                   └─→ Start capturing audio
                       └─→ User taps again
                           └─→ Stop recording
                               └─→ Convert chunks to blob
                                   └─→ Send to /converse API
                                       └─→ Receive audio blob + sessionId
                                           └─→ Play audio
                                               └─→ Ready for next turn
```

---

## 🔌 API Client (bunny-api.ts)

```typescript
// Purpose: Encapsulate all backend API calls

Constants:
├─ BASE_URL: process.env.VITE_BUNNY_API_URL ?? "http://localhost:3000"
│  └─ Configurable per environment
│  └─ Dev: localhost:3000
│  └─ Prod: Render URL (e.g., https://my-service.onrender.com)

Functions:

1. converseWithAudio(audioBlob, sessionId):
   ├─ Purpose: Send recorded audio to /converse
   ├─ Input:
   │  ├─ audioBlob: Blob from MediaRecorder (webm/opus)
   │  └─ sessionId: string | null
   ├─ Sends:
   │  ├─ POST multipart/form-data
   │  ├─ Fields: "audio" (blob), "sessionId" (string)
   │  └─ Header: X-Session-ID (if sessionId exists)
   ├─ Response:
   │  ├─ audio: Blob (wav)
   │  └─ sessionId: string | null (from X-Session-ID header)
   └─ Errors: Throw on !res.ok

2. converseWithText(message, sessionId):
   ├─ Purpose: Send text to /converse-text (no STT needed)
   ├─ Input:
   │  ├─ message: string
   │  └─ sessionId: string | null
   ├─ Sends:
   │  ├─ POST application/json
   │  ├─ Body: { message, sessionId }
   │  └─ Header: X-Session-ID (if sessionId exists)
   ├─ Response:
   │  ├─ audio: Blob (wav)
   │  └─ sessionId: string | null
   └─ Errors: Throw on !res.ok

3. checkHealth():
   ├─ Purpose: GET /health (not yet used in UI)
   ├─ Returns: boolean (true if 200 OK, false otherwise)
   ├─ Usage: Could be used for connection check before /converse
   └─ Errors: Silently return false
```

---

## 🌍 Environment Configuration

### Frontend (.env)

```env
# bunny-buddy-client/.env

# Backend URL (defaults to http://localhost:3000)
VITE_BUNNY_API_URL=http://localhost:3000
```

### Backend (.env)

```env
# .env (project root)

# API Keys
DEEPGRAM_API_KEY=<your_deepgram_key>
GEMINI_API_KEY=<your_gemini_key>

# LLM Provider
LLM_PROVIDER=local    # dev: local (Ollama)
                      # prod: gemini (Render)

# Memory
CHROMA_URL=http://localhost:8000

# Server
PORT=3000
NODE_ENV=development  # or production
```

---

## 🚀 Startup Sequence

```
DEVELOPMENT (Local):

1. Terminal 1: Start backend
   $ cd /Users/tanishqyadav/agent
   $ npm start
   └─→ Express server listening on http://localhost:3000
   └─→ Initializes Chroma connection
   └─→ Loads embedding model (first load ~10s)

2. Terminal 2: Start frontend
   $ cd bunny-buddy-client
   $ npm run dev
   └─→ Vite dev server on http://localhost:5173 (or port chosen)
   └─→ Frontend connects to backend at http://localhost:3000

3. Browser: Open http://localhost:5173
   └─→ React app loads
   └─→ Shows Bunny Buddy UI
   └─→ Ready to connect & talk

4. User clicks "Connect"
   └─→ Browser requests microphone permission
   └─→ useBunnyVoiceSession.connect() receives stream
   └─→ Status → "running"
   └─→ User can tap orb to record


PRODUCTION (Render):

1. GitHub: Push code
   └─→ Render webhook triggered

2. Render: Build Docker image
   └─→ Stage 1: Build Piper TTS (Python)
   └─→ Stage 2: Bundle Node app

3. Render: Start container
   └─→ npm start
   └─→ Server listening on port (injected by Render)
   └─→ Health check: GET /health every 30s

4. Frontend deployed separately (e.g., Vercel, Netlify)
   └─→ Built version of bunny-buddy-client/
   └─→ VITE_BUNNY_API_URL = https://<render-service-url>
   └─→ When user visits, connects to backend on Render
```

---

## 🔍 Data Flow Examples

### Example 1: Simple Greeting

```
USER ACTION: Tap orb, say "Hello", tap again

FRONTEND:
1. startTurn() → Create MediaRecorder
2. User speaks → Audio captured
3. stopTurn() → Stop recording
4. Create blob from chunks (webm)
5. converseWithAudio(blob, null)  // first time, no sessionId

HTTP REQUEST:
POST /converse
Content-Type: multipart/form-data
[Body: audio blob]

BACKEND Processing:
1. Extract blob
2. transcribeAudio() → Deepgram → "Hello"
3. generateEmbedding("Hello") → [vector]
4. retrieveRelevantMemories(sessionId, "Hello") → [] (no matches)
5. buildContextPrompt() → "You are Bunny Buddy... User said: Hello"
6. getLLMResponse() → "Hi there! I'm Bunny Buddy. How can I help?"
7. extractDurableMemory("Hello") → null (not durable)
8. textToSpeech() → WAV audio
9. addTurnToSession()
10. Return: audio + sessionId

HTTP RESPONSE:
200 OK
Content-Type: audio/wav
X-Session-ID: session_123

[Body: WAV audio data]

FRONTEND:
1. Receive response
2. sessionIdRef.current = "session_123"
3. playResponse(audio)
4. setMode("speaking")
5. Orb animates, audio plays
6. Audio ends → setMode("listening")
7. Ready for next turn (will reuse sessionId)
```

### Example 2: Follow-up with Memory

```
SAME SESSION (sessionId = "session_123")

USER ACTION: Tap orb, say "I prefer dark mode", tap again

FRONTEND:
1. toggleTurn() → startTurn()
2. User speaks → "I prefer dark mode"
3. toggleTurn() → stopTurn()
4. converseWithAudio(blob, "session_123")  // WITH sessionId

HTTP REQUEST:
POST /converse
X-Session-ID: session_123
Content-Type: multipart/form-data
[Body: audio blob + sessionId field]

BACKEND Processing:
1. Extract blob + sessionId: "session_123"
2. transcribeAudio() → "I prefer dark mode"
3. generateEmbedding("I prefer dark mode") → [vector]
4. retrieveRelevantMemories("session_123", transcript)
   └─→ Query Chroma for similar facts in this session
   └─→ Find: [] (first time mentioning preference)
5. buildContextPrompt() with empty memories
   ├─ SYSTEM_PROMPT
   ├─ RECENT_CONVERSATION (turn 1: Hello/Hi there)
   └─ CURRENT: "I prefer dark mode"
6. getLLMResponse() → "Noted! I'll remember you prefer dark mode. Sounds sleek!"
7. extractDurableMemory() (async) → "User prefers dark mode"
   └─→ Embed & store in Chroma with sessionId metadata
8. textToSpeech() → WAV
9. addTurnToSession()
   └─→ Buffer now: [Turn1, Turn2]
10. Return: audio + sessionId

HTTP RESPONSE:
200 OK
X-Session-ID: session_123
[Audio]

FRONTEND:
1. Receive & play audio
2. Conversation history shows:
   ├─ you: Voice message
   ├─ bunny: Reply
   ├─ you: Voice message
   └─ bunny: Reply
```

### Example 3: Memory Retrieval Later

```
LATER IN SAME SESSION:

USER ACTION: Say "What do I prefer?"

BACKEND Processing:
1. transcribeAudio() → "What do I prefer?"
2. generateEmbedding() → [vector for question]
3. retrieveRelevantMemories("session_123", "What do I prefer?")
   └─→ Query Chroma: similarity search
   └─→ Find: "User prefers dark mode" (distance 0.35 < 0.95 threshold)
   └─→ Return: ["User prefers dark mode"]
4. buildContextPrompt():
   RELEVANT MEMORIES:
   - User prefers dark mode
   
   RECENT CONVERSATION:
   [Last up to 10 turns]
   
   CURRENT:
   What do I prefer?
5. getLLMResponse() → "You mentioned you prefer dark mode! It's a great choice for reducing eye strain."
6. textToSpeech() → WAV
7. Return: audio

RESULT: LLM knew about preference because of memory retrieval!
```

---

## 🎯 Key Connection Points

### 1. Frontend → Backend Endpoint Mapping

| Frontend Function | HTTP Method | Backend Endpoint | Purpose |
|---|---|---|---|
| `converseWithAudio(blob, sid)` | POST | `/converse` | Voice interaction |
| `converseWithText(text, sid)` | POST | `/converse-text` | Text fallback |
| `checkHealth()` | GET | `/health` | Service status |

### 2. Session ID Persistence

```
Session Flow:
├─ First interaction: sessionId = null
│  └─ Backend generates → sessionId = "session_abc123"
├─ Backend sends: X-Session-ID: session_abc123
├─ Frontend stores: sessionIdRef.current = "session_abc123"
├─ Next interaction: Send sessionId with request
│  └─ Backend retrieves existing session buffer
│  └─ Backend queries memory by sessionId
├─ Backend returns: X-Session-ID: session_abc123 (same)
└─ Repeats for entire session
```

### 3. Error Handling

**Frontend:**
```typescript
try {
  const result = await converseWithAudio(blob, sessionId);
  // success
} catch (error) {
  setError(error.message);
  setStatus("running");  // Reset status
  setMode("listening");   // Back to listening
}
```

**Backend:**
```javascript
if (!res.ok) {
  res.status(400).json({
    error: "Invalid audio format",
    step: "Deepgram STT"
  });
}
```

---

## 🔧 Integration Checklist

- ✅ Frontend running on `http://localhost:5173` (or 3000 if configured)
- ✅ Backend running on `http://localhost:3000`
- ✅ Backend `.env` configured with API keys
- ✅ Chroma service running (local or cloud)
- ✅ Ollama running for local LLM (dev mode)
- ✅ Frontend `.env` points to backend URL
- ✅ CORS enabled on backend (allow localhost:5173)
- ✅ User grants microphone permission
- ✅ Audio recording working (MediaRecorder)
- ✅ API calls returning 200 OK
- ✅ Session ID persisting across turns
- ✅ Memory working (extracted & retrieved)

---

## 📊 Performance Metrics

| Operation | Time | Bottleneck |
|---|---|---|
| Audio capture → stop | ~2 seconds | User speaking |
| Send to backend | <0.5s | Network |
| Deepgram STT | 1-3s | API latency |
| Embedding generation | 0.5-1s | CPU (Xenova) |
| Memory retrieval | 0.1s | Vector DB query |
| LLM inference | 2-5s | API (Gemini/Ollama) |
| Piper TTS | 1-2s | CPU synthesis |
| **Total E2E** | **~7-14s** | LLM is dominant |

---

## 🐛 Common Issues & Solutions

| Issue | Cause | Solution |
|---|---|---|
| CORS error | Backend not allowing localhost:5173 | Check `app.use(cors(...))` in server.js |
| "Couldn't reach Bunny Buddy" | Backend down or wrong URL | Check VITE_BUNNY_API_URL, start backend |
| Microphone permission denied | User denied access | Browser settings → allow microphone |
| "Deepgram error" | API key invalid or quota exceeded | Check DEEPGRAM_API_KEY in .env |
| No audio output | Piper TTS failed | Check piper-venv/bin/python exists |
| Session ID not reusing | Old sessionId lost | Ensure sessionIdRef.current persists |

---

## 🚀 Deployment Integration

### Frontend Deployment (e.g., Vercel)

```env
# .env.production
VITE_BUNNY_API_URL=https://my-bunny-service.onrender.com
```

### Backend Deployment (Render)

```yaml
# render.yaml
envVars:
  - key: DEEPGRAM_API_KEY
    value: <actual-key>
  - key: GEMINI_API_KEY
    value: <actual-key>
  - key: CHROMA_URL
    value: https://api.trychroma.com
  - key: CHROMA_API_KEY
    value: <actual-key>
  - key: LLM_PROVIDER
    value: gemini  # Force production LLM
```

---

## ✅ Summary

The **Bunny Buddy Client** connects to the backend through:

1. **WebGL Orb UI** → Shows connection state
2. **React Hook** (`useBunnyVoiceSession`) → Manages audio capture & state
3. **API Client** (`bunny-api.ts`) → Makes HTTP requests
4. **Express Backend** → Processes requests through STT → LLM → TTS pipeline
5. **Session Management** → Maintains conversation context via sessionId
6. **Memory System** → Stores & retrieves durable facts

The flow is: **Microphone → Blob → HTTP POST → Processing → WAV → Audio Playback**

**Performance**: ~7-14 seconds end-to-end (dominated by LLM latency).

---

**Version**: 1.0  
**Last Updated**: August 28, 2026  
**Status**: Complete Integration ✅
