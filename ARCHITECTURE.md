# Bunny Buddy - System Architecture

## 📐 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT (Web/Mobile)                               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   HTTP/REST API        │
                    │  Multipart/JSON        │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────▼────────────────────────┐
        │      Express.js Server (Node.js 20)            │
        │           Bunny Buddy Backend                   │
        └────────────────────────┬────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
    ┌─────────┐         ┌──────────────┐       ┌──────────────┐
    │ Deepgram│         │  Gemini/     │       │ Chroma DB    │
    │  (STT)  │         │  Ollama      │       │  (Memory)    │
    │  API    │         │  (LLM)       │       │              │
    └─────────┘         └──────────────┘       └──────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Piper TTS Engine      │
                    │   (Local Python)        │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Audio Output (WAV)    │
                    │   Returned to Client    │
                    └────────────────────────┘
```

---

## 🏗️ Detailed System Architecture

### 1. Request Processing Pipeline

```
USER AUDIO INPUT
    │
    ▼
┌─────────────────────────────────────┐
│  1. REQUEST VALIDATION              │
│  - Audio file size check            │
│  - Format validation (WAV/MP3/etc)  │
│  - Session ID extraction            │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  2. DEEPGRAM STT SERVICE            │
│  - Send audio to Deepgram API       │
│  - Receive transcript text          │
│  - Extract confidence scores        │
│  - Handle silence detection         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  3. EMBEDDING GENERATION            │
│  - Load Xenova/all-MiniLM-L6-v2     │
│  - Convert transcript to vector     │
│  - Local computation (no API)       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  4. MEMORY RETRIEVAL                │
│  - Query Chroma vector store        │
│  - Find top-3 relevant memories     │
│  - Filter by session ID             │
│  - Apply similarity threshold       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  5. CONTEXT BUILDING                │
│  - System prompt                    │
│  - Retrieved memories               │
│  - Recent 10 conversation turns     │
│  - Current user message             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  6. LLM INFERENCE                   │
│  - Route: Gemini (prod) or          │
│           Ollama (dev)              │
│  - Generate natural response        │
│  - Maintain conversation context    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  7. ASYNC MEMORY EXTRACTION         │
│  - Analyze user message             │
│  - Extract durable facts            │
│  - Non-blocking (background)        │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  8. MEMORY STORAGE                  │
│  - Embed extracted fact             │
│  - Store in Chroma                  │
│  - Add session metadata             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  9. TEXT-TO-SPEECH                  │
│  - Invoke Piper TTS engine          │
│  - Use voice model                  │
│  - Generate audio WAV file          │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  10. SESSION BUFFER UPDATE          │
│  - Add (user, assistant) turn       │
│  - Keep last 10 turns               │
│  - Remove oldest if > 10            │
└────────────┬────────────────────────┘
             │
             ▼
    AUDIO OUTPUT (WAV)
    + X-Session-ID Header
```

---

## 🔌 Component Architecture

### A. Express.js Server Core

```javascript
server.js (Main Application)
├── Initialization
│   ├── Load environment variables
│   ├── Initialize Chroma connection
│   ├── Initialize Deepgram client
│   └── Initialize Gemini/Ollama client
│
├── Middleware
│   ├── CORS (cross-origin requests)
│   ├── JSON parser
│   ├── Form data parser (fileupload)
│   └── Static file serving
│
├── Route Handlers
│   ├── POST /converse (main endpoint)
│   ├── POST /converse-text (text input)
│   ├── GET /health (status check)
│   └── GET / (404 response)
│
└── Support Functions
    ├── STT: transcribeAudio()
    ├── Embedding: generateEmbedding()
    ├── Memory: retrieveRelevantMemories()
    ├── LLM: getLLMResponse()
    ├── TTS: textToSpeech()
    └── Session: getSession()
```

### B. Memory Management System

```
┌────────────────────────────────────────────────────────────┐
│           MEMORY MANAGEMENT ARCHITECTURE                   │
└────────────────────────────────────────────────────────────┘

SESSION MEMORY (In-Memory, Ephemeral)
├── Stores: Last 10 conversation turns
├── Structure:
│   └── session[sessionId].turns = [
│       { user: "...", assistant: "..." },
│       { user: "...", assistant: "..." },
│       ... (max 10 items)
│   ]
├── Lifespan: Duration of server uptime
└── Access: Ultra-fast (in RAM)

    │
    │ ┌─────────────────────────────────────────┐
    │ │   DURABLE MEMORY EXTRACTION             │
    │ │   (Background, Non-blocking)            │
    │ │                                         │
    │ │   analyzeMessage(userMessage) → bool    │
    │ │   Filter: preferences, instructions    │
    │ │   Ignore: questions, greetings         │
    │ └────────────────┬────────────────────────┘
    │                  │
    │                  ▼
    │ ┌─────────────────────────────────────────┐
    │ │   EMBEDDING GENERATION                  │
    │ │   (Local, Xenova)                       │
    │ │                                         │
    │ │   fact → embedding (vector)             │
    │ │   No API cost                           │
    │ └────────────────┬────────────────────────┘
    │                  │
    │                  ▼
    ▼ ┌─────────────────────────────────────────┐
      │   PERSISTENT VECTOR STORE               │
      │   (Chroma DB)                           │
      │                                         │
      │   Structure:                            │
      │   ├── Collection: "memories"            │
      │   ├── Documents: [facts, ...] (text)    │
      │   ├── Embeddings: [vectors, ...]        │
      │   ├── Metadata: {sessionId, timestamp}  │
      │   └── IDs: unique identifiers           │
      │                                         │
      │   Dev: SQLite at ./data/chroma/         │
      │   Prod: Chroma Cloud (API)              │
      │                                         │
      │   Lifespan: Indefinite                  │
      │   Access: ~100ms per query              │
      └────────────────┬─────────────────────────┘
                       │
                       │ For each new message:
                       │ Query for top-3 similar
                       │
                       ▼
      ┌─────────────────────────────────────────┐
      │   MEMORY RETRIEVAL                      │
      │   (Semantic Search)                     │
      │                                         │
      │   1. Embed new message                  │
      │   2. Find similar vectors               │
      │   3. Filter by session ID               │
      │   4. Apply threshold (< 0.95)           │
      │   5. Return top-3 facts                 │
      │                                         │
      │   Output: List of relevant memories     │
      └────────────────┬────────────────────────┘
                       │
                       ▼
      ┌─────────────────────────────────────────┐
      │   CONTEXT AUGMENTATION                  │
      │   Inject into LLM Prompt                │
      │                                         │
      │   Prompt = (                            │
      │     system_prompt +                     │
      │     retrieved_memories +                │
      │     recent_10_turns +                   │
      │     current_message                     │
      │   )                                     │
      └─────────────────────────────────────────┘
```

### C. LLM Provider Architecture

```
┌──────────────────────────────────────────────────────────┐
│            LLM PROVIDER ABSTRACTION                      │
└──────────────────────────────────────────────────────────┘

    LLM_PROVIDER environment variable
            │
            ├─────── "gemini" ──────────┐
            │                           ▼
            │                ┌────────────────────────┐
            │                │ GOOGLE GEMINI API      │
            │                ├────────────────────────┤
            │                │ Endpoint: generative   │
            │                │ Model: gemini-3.6-flash
            │                │ Cost: Pay-per-API      │
            │                │ Speed: 2-5 seconds     │
            │                │ Quality: Enterprise    │
            │                │ Context: 1M tokens     │
            │                └────────────────────────┘
            │
            └─────── "local" ───────────┐
                                        ▼
                             ┌────────────────────────┐
                             │ OLLAMA LOCAL           │
                             ├────────────────────────┤
                             │ Endpoint: localhost    │
                             │ Model: llama3.2        │
                             │ Cost: Free             │
                             │ Speed: 1-3 seconds     │
                             │ Quality: Good          │
                             │ Privacy: Offline       │
                             └────────────────────────┘

    Both routed through:
    getLLMResponseWithContext(contextPrompt) → response
```

### D. TTS Engine Architecture

```
┌──────────────────────────────────────────────────────────┐
│            PIPER TTS ARCHITECTURE                        │
└──────────────────────────────────────────────────────────┘

    LLM Response Text
            │
            ▼
    ┌──────────────────────────┐
    │ PIPER TTS ENGINE         │
    │ (Python 3.11)            │
    │                          │
    │ Location:                │
    │ ~/piper-venv/bin/piper   │
    │                          │
    │ Voice Model:             │
    │ en_US-lessac-medium.onnx │
    │ Config: .onnx.json       │
    │                          │
    │ Input: Text              │
    │ Output: WAV audio        │
    │ Sample Rate: 22.05 kHz   │
    │ Mono/Stereo: Mono        │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ WAV AUDIO FILE           │
    │ Temporary storage        │
    │ Clean up after send      │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ RETURN TO CLIENT         │
    │ Content-Type: audio/wav  │
    └──────────────────────────┘

    Performance:
    - Generation: ~1-2 seconds per response
    - Quality: Natural sounding voice
    - Cost: $0 (local, no API)
```

---

## 🔄 Data Flow Diagrams

### Flow 1: Complete Conversation Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│                   NEW CONVERSATION                              │
└─────────────────────────────────────────────────────────────────┘

Step 1: USER SPEAKS
   │ Audio File (WAV/MP3)
   │ + sessionId (optional)
   ▼
Step 2: DEEPGRAM STT
   │ Deepgram API processes audio
   │ Returns transcript text
   ▼
Step 3: EMBEDDING GENERATION
   │ Xenova/all-MiniLM-L6-v2
   │ Convert text → vector
   ▼
Step 4: MEMORY SEARCH
   │ Query Chroma DB
   │ Find similar past facts
   │ Returns top-3
   ▼
Step 5: BUILD CONTEXT
   Combine:
   ├── System prompt
   ├── Retrieved memories
   ├── Last 10 conversation turns
   └── Current user message
   ▼
Step 6: LLM INFERENCE
   │ Send context to LLM
   │ Receive response text
   ▼
Step 7: ASYNC EXTRACT
   │ Analyze user message
   │ Extract durable facts
   │ Store in background
   │ (Non-blocking)
   ▼
Step 8: TTS SYNTHESIS
   │ Piper TTS converts response
   │ to audio (WAV)
   ▼
Step 9: UPDATE SESSION
   │ Add (user, assistant) turn
   │ Keep 10-turn rolling buffer
   ▼
Step 10: RETURN AUDIO
   │ Send WAV file
   │ Include X-Session-ID
   └─→ CLIENT RECEIVES RESPONSE
```

### Flow 2: Memory Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                   MEMORY LIFECYCLE                              │
└─────────────────────────────────────────────────────────────────┘

USER MESSAGE: "I prefer dark mode"
   │
   ▼
EXTRACTION (Background)
   "Is this a durable fact?"
   ✓ Yes → "User prefers dark mode"
   │
   ▼
EMBEDDING
   Fact → Vector representation
   │
   ▼
STORAGE (Chroma)
   Store with metadata:
   ├── id: "mem_xyz789"
   ├── text: "User prefers dark mode"
   ├── embedding: [0.12, 0.45, ...]
   ├── sessionId: "session_abc123"
   └── timestamp: "2026-08-28T..."
   │
   ▼
LATER: NEW USER MESSAGE
   "What are my preferences?"
   │
   ▼
RETRIEVAL
   1. Embed new message
   2. Search similar vectors
   3. Find match: distance 0.45 < 0.95 ✓
   4. Return: "User prefers dark mode"
   │
   ▼
CONTEXT INJECTION
   LLM Prompt includes:
   "RELEVANT MEMORIES:
    - User prefers dark mode"
   │
   ▼
LLM RESPONSE
   "Based on what I remember,
    you prefer dark mode!"
```

---

## 📊 Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENT                                  │
│                   (Browser/Mobile)                             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                    HTTP/REST
                         │
        ┌────────────────▼────────────────┐
        │    EXPRESS.JS SERVER LAYER      │
        │  (Request/Response Handling)    │
        └────────────────┬────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐     ┌─────────┐    ┌──────────┐
    │SERVICES│     │MEMORY   │    │UTILITIES │
    │ LAYER  │     │ LAYER   │    │ LAYER    │
    └────────┘     └─────────┘    └──────────┘
         │               │               │
         ▼               ▼               ▼
    ┌────────┐     ┌─────────┐    ┌──────────┐
    │  STT   │     │ SESSION │    │EMBEDDING │
    │Deepgram│     │  BUFFER │    │ Xenova   │
    └────────┘     └─────────┘    └──────────┘
         │               │
         ▼               ▼
    ┌────────┐     ┌─────────┐
    │  LLM   │     │CHROMA   │
    │Gemini/ │     │  VECTOR │
    │Ollama  │     │  STORE  │
    └────────┘     └─────────┘
         │
         ▼
    ┌────────┐
    │  TTS   │
    │ Piper  │
    └────────┘
```

---

## 🗂️ File Structure & Dependencies

```
project-root/
│
├── server.js
│   ├── Imports:
│   │   ├── express (web framework)
│   │   ├── axios (HTTP client)
│   │   ├── dotenv (env vars)
│   │   ├── chromadb (vector DB)
│   │   ├── @xenova/transformers (embeddings)
│   │   └── fs, path (Node.js)
│   │
│   ├── Main functions:
│   │   ├── async initializeChroma()
│   │   ├── async generateEmbedding(text)
│   │   ├── function getSession(sessionId)
│   │   ├── async retrieveRelevantMemories()
│   │   ├── async extractDurableMemory()
│   │   ├── async storeMemory()
│   │   ├── function buildContextPrompt()
│   │   ├── async transcribeAudio()
│   │   ├── async getLLMResponseWithContext()
│   │   ├── async getOllamaResponse()
│   │   ├── async getGeminiResponse()
│   │   └── async textToSpeech()
│   │
│   └── Routes:
│       ├── POST /converse (main endpoint)
│       ├── POST /converse-text (text input)
│       ├── GET /health (status)
│       └── GET / (404)
│
├── tools.js
│   ├── Tool definitions (weather, search, etc.)
│   └── Exported for LLM function calling
│
├── package.json
│   ├── Dependencies:
│   │   ├── express@^4.18.2
│   │   ├── axios@^1.4.0
│   │   ├── dotenv@^16.0.3
│   │   ├── chromadb@^1.5.11
│   │   ├── @xenova/transformers@^2.6.1
│   │   ├── cors@^2.8.5
│   │   └── express-fileupload@^1.4.0
│   │
│   └── Scripts:
│       ├── start (npm start)
│       ├── dev (auto-reload)
│       └── check (dependency check)
│
├── .env
│   ├── DEEPGRAM_API_KEY
│   ├── GEMINI_API_KEY
│   ├── CHROMA_URL
│   ├── CHROMA_API_KEY
│   ├── LLM_PROVIDER (gemini | local)
│   └── PORT (3000)
│
├── Dockerfile
│   ├── Stage 1: Python 3.11
│   │   └── Build Piper TTS
│   │
│   └── Stage 2: Node 20
│       ├── Install runtime deps
│       ├── Copy Node app
│       ├── Copy Piper from Stage 1
│       └── Expose 3000
│
├── render.yaml
│   ├── Service definition
│   ├── Build config
│   ├── Health check
│   ├── Environment variables
│   └── Dockerfile path
│
├── docker-compose.yml
│   ├── Service: node-app (Port 3000)
│   ├── Service: chroma (Port 8000)
│   ├── Service: ollama (Port 11434)
│   └── Networks: internal
│
├── piper-venv/
│   ├── bin/
│   │   ├── python
│   │   └── piper
│   └── lib/ (Piper dependencies)
│
├── piper-voices/
│   ├── en_US-lessac-medium.onnx
│   └── en_US-lessac-medium.onnx.json
│
└── data/
    └── chroma/ (Persistent vector store - dev)
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           SECURITY & ISOLATION LAYERS                       │
└─────────────────────────────────────────────────────────────┘

API Keys
  ├── Stored: .env (not in git)
  ├── Loaded: process.env
  ├── Used: Not logged
  └── Rotatable: Via dashboard

Session Isolation
  ├── Each session: Separate memory
  ├── Queries: Filtered by sessionId
  ├── No data: Crosses sessions
  └── Storage: Isolated Chroma collection

CORS Control
  ├── Allowed origins: Configured
  ├── Credentials: Explicit settings
  ├── Methods: POST, GET only
  └── Headers: JSON/multipart

Error Handling
  ├── Detailed: Dev mode (logs)
  ├── Sanitized: Prod mode
  ├── No secrets: In error responses
  └── Rate limiting: Not implemented yet

Data Privacy
  ├── Transcripts: Stored temporarily
  ├── Embeddings: Never logged
  ├── Memories: In Chroma only
  └── Cleanup: Automatic
```

---

## 📈 Scalability Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            SCALABILITY CONSIDERATIONS                       │
└─────────────────────────────────────────────────────────────┘

Single Server Limitations
  ├── Sessions: In-memory (lost on restart)
  ├── Throughput: ~100 req/min
  ├── Memory: Grows with sessions
  └── Latency: Varies with LLM

Scaling Strategies

1. HORIZONTAL SCALING
   ├── Load balance multiple servers
   ├── Session affinity (sticky sessions)
   ├── Shared Chroma Cloud instance
   └── Stateless except session buffer

2. VERTICAL SCALING
   ├── Increase Render instance size
   ├── More CPU for LLM inference
   ├── More memory for embeddings
   └── Better cache locality

3. SESSION PERSISTENCE
   ├── Move buffer to Redis (optional)
   ├── Enable session migration
   ├── Survive server restarts
   └── Better availability

4. MEMORY OPTIMIZATION
   ├── Compress embeddings
   ├── Prune old memories
   ├── Batch vector operations
   └── Index optimization

Current Single-Instance Architecture
  ┌─────────────────────────────────┐
  │  Render Container (2GB RAM)     │
  │  ┌─────────────────────────────┐│
  │  │ Express.js Server           ││
  │  │ ├─ Session Buffer           ││
  │  │ ├─ Embedding Model (loaded) ││
  │  │ └─ Piper TTS                ││
  │  └─────────────────────────────┘│
  └─────────────────────────────────┘
         │
         ├─→ Chroma Cloud (Elastic)
         ├─→ Deepgram API (Elastic)
         ├─→ Gemini API (Elastic)
         └─→ Ollama (N/A in prod)
```

---

## 🔧 Deployment Architecture

### Development Environment
```
Local Machine
├── Node.js 20
├── Python 3.11
├── docker-compose up
│   ├── Express server (localhost:3000)
│   ├── Chroma server (localhost:8000)
│   └── Ollama server (localhost:11434)
└── .env with local settings
```

### Production Environment (Render)
```
Render Container
├── Multi-stage Docker Build
│   ├── Stage 1: Python 3.11
│   │   └── Build Piper TTS
│   └── Stage 2: Node 20
│       ├── Bundle app
│       ├── Copy Piper
│       └── Start server
├── Health checks (30s interval)
├── Automatic restarts on failure
└── Environment variables injected
```

---

## 🎯 Key Design Patterns

### 1. **Request-Response Pattern**
- HTTP POST with audio/text input
- Synchronous response with audio output
- No streaming (could add WebSocket)

### 2. **Session Management Pattern**
- SessionId-based conversation tracking
- Automatic generation if not provided
- Per-session memory isolation

### 3. **Pipeline Pattern**
- Sequential processing steps
- Each step independent
- Easy to add/remove steps

### 4. **Async Background Processing**
- Memory extraction non-blocking
- Doesn't delay response
- Eventual consistency

### 5. **Provider Abstraction**
- Swappable LLM providers
- Environment-driven routing
- Identical interface

### 6. **Vector Similarity Search**
- Semantic matching via embeddings
- Threshold-based filtering
- Top-K retrieval

---

## 📊 Performance Characteristics

```
Operation              Time      Cost      Notes
─────────────────────────────────────────────────────
STT (Deepgram)        1-3s      $0.0043   Per minute
Embedding Gen         0.5-1s    $0        Local
Memory Query          0.1s      $0        Vector search
LLM Response          2-5s      $0.001    Via Gemini
TTS Synthesis         1-2s      $0        Local Piper
Total E2E             5-12s     ~$0.006   Per interaction
```

---

## 🔮 Future Architecture Enhancements

```
Potential Improvements

1. STREAMING
   ├── WebSocket connection
   ├── Real-time audio streaming
   ├── Lower latency
   └── Better UX

2. DISTRIBUTED SESSIONS
   ├── Redis session store
   ├── Multi-server support
   ├── Session migration
   └── High availability

3. ADVANCED MEMORY
   ├── Memory summarization
   ├── Hierarchical storage
   ├── Forgetting mechanisms
   ├── Temporal indexing
   └── Semantic clustering

4. MULTI-LLM SUPPORT
   ├── LLaMA integration
   ├── Claude support
   ├── Model comparison
   ├── Ensemble methods
   └── A/B testing framework

5. ENHANCED VOICE
   ├── Voice cloning
   ├── Emotion detection
   ├── Multiple voice models
   ├── Accent selection
   └── Gender/age control
```

---

## ✅ Architecture Checklist

- ✅ Modular component design
- ✅ Clear separation of concerns
- ✅ Stateless API (mostly)
- ✅ Async memory operations
- ✅ Error handling & recovery
- ✅ CORS & security
- ✅ Environment-driven config
- ✅ Health monitoring
- ✅ Scalability considered
- ✅ Documentation complete

---

**Version**: 3.0  
**Last Updated**: August 28, 2026  
**Status**: Production Ready ✅
