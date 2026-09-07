# Voice Assistant Backend

A voice assistant backend with conversation memory that implements the STT → LLM → TTS pipeline.

## Features

### Phase 1: Core Pipeline
- **Speech-to-Text**: Deepgram API for audio transcription
- **LLM Processing**: Local Ollama (llama3.2) or cloud Gemini 3.6 Flash
- **Text-to-Speech**: Piper (local TTS) for natural voice synthesis
- **Single Endpoint**: POST `/converse` - send audio, get audio back

### Phase 2: Conversation Memory ✨
- **Session-based Memory**: Each session maintains its own conversation history
- **Rolling 10-turn Buffer**: Automatically keeps the last 10 conversation turns
- **Persistent Vector Store**: Chroma DB for long-term memory storage
- **Smart Memory Extraction**: Automatically identifies and stores durable facts
- **Contextual Retrieval**: Top-3 relevant memories injected into each conversation
- **Session Isolation**: Different users/sessions have separate memories

### Phase 3: Local LLM ✨ NEW
- **Ollama Integration**: Run LLM locally with no API costs
- **Provider Fallback**: Switch between local (Ollama) and cloud (Gemini)
- **Cost Efficiency**: Free local inference with llama3.2 (3.2B parameters)
- **Privacy**: All LLM processing can happen locally
- **Flexible**: Easy A/B comparison via LLM_PROVIDER env variable

## Architecture

### Phase 1 Pipeline
```
Audio Input → Deepgram STT → Gemini 3.6 Flash → Piper TTS → Audio Output (WAV)
```

### Phase 2 Enhanced Flow
```
Audio Input
   ↓
Deepgram STT (transcription)
   ↓
Generate Embedding
   ↓
Chroma Query (retrieve top-3 relevant memories)
   ↓
Build Context (memories + rolling 10 turns + current message)
   ↓
Gemini Response
   ↓
Memory Extraction (background, non-blocking)
   ↓
Store Durable Memory (if extracted)
   ↓
Piper TTS
   ↓
Audio Output (WAV)
```

## Setup

### Prerequisites

1. **Node.js** (v18 or higher recommended)
2. **Python with Piper TTS** - Local text-to-speech
   - Piper environment: `~/agent/piper-venv/`
   - Piper model: `~/agent/piper-voices/en_US-lessac-medium.onnx`

### Installation

1. **Install dependencies:**
   ```bash
   npm install --legacy-peer-deps
   ```
   
   Note: `--legacy-peer-deps` is required due to chromadb peer dependency conflicts.

2. **Configure API keys:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   **Verify your setup:**
   ```bash
   npm run check
   ```

3. **Start the server:**
   ```bash
   npm start
   ```

   Or for development with auto-reload:
   ```bash
   npm run dev
   ```

   On first startup, the server will:
   - Initialize Chroma vector store at `./data/chroma/`
   - Load the embedding model (Xenova/all-MiniLM-L6-v2)
   - This may take 10-20 seconds on first run

## API Endpoints

### POST `/converse`

Main endpoint for voice interactions with conversation memory.

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `audio` (required): Audio file (supports WAV, MP3, FLAC, etc.)
  - `sessionId` (optional): Session identifier for conversation continuity

**OR use header:**
- `X-Session-ID`: Session identifier

**Response:**
- Content-Type: `audio/wav`
- Body: Audio file (WAV) with the assistant's spoken response
- Headers:
  - `X-Session-ID`: The session ID used (generated if not provided)

**Session Management:**
- If no `sessionId` is provided, the server generates one automatically
- Use the same `sessionId` across requests to maintain conversation context
- Each session has:
  - Rolling 10-turn conversation buffer (in-memory)
  - Persistent durable memories (in Chroma)

**Example with curl (new session):**
```bash
curl -X POST http://localhost:3000/converse \
  -F "audio=@recording.wav" \
  --output response.wav
```

**Example with curl (specific session):**
```bash
SESSION_ID="my-session-123"

curl -X POST http://localhost:3000/converse \
  -F "audio=@recording.wav" \
  -F "sessionId=$SESSION_ID" \
  --output response.wav
```

**Example with JavaScript:**
```javascript
const formData = new FormData();
formData.append('audio', audioBlob, 'recording.wav');
formData.append('sessionId', 'my-session-123');

const response = await fetch('http://localhost:3000/converse', {
  method: 'POST',
  body: formData
});

const sessionId = response.headers.get('X-Session-ID');
const audioBlob = await response.blob();
const audioUrl = URL.createObjectURL(audioBlob);
// Play audioUrl
```

### GET `/health`

Check service status and API key configuration.

**Response:**
```json
{
  "status": "ok",
  "services": {
    "deepgram": true,
    "gemini": true,
    "piper": true,
    "chroma": true
  }
}
```

## Memory System

### How It Works

1. **Rolling Conversation Buffer (10 turns)**
   - Each session maintains the last 10 conversation turns in memory
   - Turns are user-assistant pairs
   - When turn 11 is added, turn 1 is automatically removed
   - Used to provide recent conversation context to Gemini

2. **Durable Memory Extraction**
   - After each assistant response, the system analyzes the user's message
   - Determines if it contains a durable fact worth remembering:
     - User preferences ("I prefer dark mode")
     - Personal details ("I usually work late at night")
     - Recurring tasks ("Remind me that I like concise answers")
   - Does NOT store:
     - Questions ("What's the capital of France?")
     - Greetings ("Hello", "Thanks")
     - Temporary content
   - Extraction runs in the background and doesn't delay the audio response

3. **Vector Store (Chroma)**
   - Stores durable memories persistently across server restarts
   - Each memory has:
     - Unique ID
     - Memory text
     - Embedding vector (for semantic search)
     - Metadata (sessionId, type, timestamp)
   - Location: `./data/chroma/`

4. **Memory Retrieval**
   - For each user message, the system:
     - Generates an embedding of the transcript
     - Queries Chroma for the top-3 most relevant memories
     - Only retrieves memories belonging to the current session
   - Retrieved memories are injected into the Gemini prompt

5. **Session Isolation**
   - Each session has its own:
     - Conversation buffer
     - Set of durable memories
   - Sessions never share or leak information between each other

### Embedding Model

- Uses `Xenova/all-MiniLM-L6-v2` from @xenova/transformers
- Runs locally (no API calls, no cost)
- First load takes ~10 seconds, then cached
- Used for both storing and retrieving memories

## Error Handling

The API returns appropriate error responses:

- **400 Bad Request**: Missing audio file or no speech detected
- **500 Internal Server Error**: API failures (includes error step: STT, LLM, or TTS)

Example error response:
```json
{
  "error": "Internal server error",
  "message": "API key is invalid",
  "step": "STT (Deepgram)"
}
```

## API Keys Required

1. **Deepgram** - https://deepgram.com/
   - Sign up and get API key from dashboard
   - Used for speech-to-text transcription
   
2. **Google Gemini** - https://ai.google.dev/
   - Sign up for Google AI Studio
   - Create API key from the API keys section
   - Used for LLM responses and memory extraction

**Note**: Piper TTS runs locally and requires no API key.

## Configuration

Environment variables in `.env`:

- `DEEPGRAM_API_KEY` - Deepgram API key (required)
- `GEMINI_API_KEY` - Google Gemini API key (required)
- `PORT` - Server port (optional, defaults to 3000)

### Data Storage

- **Chroma Vector Store**: `./data/chroma/` (persistent, not committed to git)
- **Session Memory**: In-memory (lost on server restart)
- **Temporary TTS files**: `temp-tts-*.wav` (automatically cleaned up)

## Testing

### Quick Test (Phase 1 Pipeline)

Test the basic pipeline without memory:

```bash
# Use the provided test script
./test-curl.sh

# Or manually:
curl -X POST http://localhost:3000/converse \
  -F "audio=@test2.wav" \
  --output response.wav

# Play response (macOS)
afplay response.wav
```

### Phase 2 Memory Tests

Run automated tests:

```bash
./test-phase2.sh
```

This tests:
- New session creation
- Conversation history retention
- Session isolation
- Session ID auto-generation

### Manual Memory Testing

#### Test 1: Durable Memory Storage

```bash
SESSION_ID="memory-test-1"

# Say: "I prefer dark mode"
curl -X POST http://localhost:3000/converse \
  -F "audio=@preference.wav" \
  -F "sessionId=$SESSION_ID" \
  -o response1.wav

# Check server logs for:
# [Memory] Extracted durable fact: "User prefers dark mode"
# [Memory] Stored memory: mem_xxxxx
```

#### Test 2: Memory Retrieval

```bash
# Say: "What do I prefer?"
curl -X POST http://localhost:3000/converse \
  -F "audio=@question.wav" \
  -F "sessionId=$SESSION_ID" \
  -o response2.wav

# Check server logs for:
# [Memory] Retrieved: 1 memories
# Assistant should mention dark mode in response
```

#### Test 3: Rolling Buffer (10 turns)

```bash
# Send 11 requests with same sessionId
for i in {1..11}; do
  curl -X POST http://localhost:3000/converse \
    -F "audio=@test2.wav" \
    -F "sessionId=buffer-test" \
    -o response-$i.wav
done

# On request 11, server logs should show:
# [Memory] Removed oldest turn, kept last 10
```

#### Test 4: Session Isolation

```bash
# Session A stores a preference
curl -X POST http://localhost:3000/converse \
  -F "audio=@pizza.wav" \
  -F "sessionId=session-a" \
  -o a1.wav

# Session B asks about it
curl -X POST http://localhost:3000/converse \
  -F "audio=@what-food.wav" \
  -F "sessionId=session-b" \
  -o b1.wav

# Session B should NOT know about Session A's preference
```

#### Test 5: Persistence After Restart

```bash
SESSION_ID="persistence-test"

# 1. Store a memory
curl -X POST http://localhost:3000/converse \
  -F "audio=@preference.wav" \
  -F "sessionId=$SESSION_ID" \
  -o before-restart.wav

# 2. Restart server
# Ctrl+C to stop, then: npm start

# 3. Query the memory
curl -X POST http://localhost:3000/converse \
  -F "audio=@what-preference.wav" \
  -F "sessionId=$SESSION_ID" \
  -o after-restart.wav

# Memory should still be retrieved from Chroma
```

### Observing Memory Operations

Watch server logs for memory operations:

```
[Memory] Session: session_abc123 - New session created
[Memory] Session: session_abc123 - Retrieved: 2 memories
[Memory] Extracted durable fact: "User prefers concise answers"
[Memory] Stored memory: mem_xyz789 for session session_abc123
[Memory] Session: session_abc123 - Removed oldest turn, kept last 10
```

## Current Features

### Phase 1: Core Pipeline ✅
- Speech-to-text transcription (Deepgram)
- LLM conversation (Gemini 3.6 Flash)
- Text-to-speech synthesis (Piper local)
- Simple request/response flow

### Phase 2: Conversation Memory ✅
- Session-based memory management
- Rolling 10-turn conversation buffer
- Persistent vector store (Chroma)
- Automatic durable memory extraction
- Top-3 semantic memory retrieval
- Session isolation
- Local embeddings (no API cost)

## Limitations

- No streaming support (full request/response only)
- No tool use or function calling
- Session memory (rolling buffer) is lost on server restart
- Durable memories persist but conversation history doesn't
- Single-language support (English)
- No user authentication

## Next Steps (Future Phases)

To extend this foundation:
- Phase 3: Streaming support for lower latency
- Add function calling/tools (web search, calendar, etc.)
- Implement WebSocket for real-time audio
- Add user authentication
- Multi-language support
- Voice activity detection
- Advanced memory management (summarization, forgetting)
