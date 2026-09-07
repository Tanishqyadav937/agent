# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Voice Assistant API                      │
└─────────────────────────────────────────────────────────────┘

Input: Audio File/Stream (WAV, MP3, FLAC, etc.)
                    ↓
        ┌───────────────────────┐
        │   Express Server      │
        │   POST /converse      │
        └───────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  Step 1: Deepgram     │
        │  Speech-to-Text       │
        │  ─────────────────    │
        │  Audio → Text         │
        └───────────────────────┘
                    ↓
            "User transcript"
                    ↓
        ┌───────────────────────┐
        │  Step 2: Gemini API   │
        │  Language Model       │
        │  ─────────────────    │
        │  Text → Response      │
        └───────────────────────┘
                    ↓
        "Assistant response text"
                    ↓
        ┌───────────────────────┐
        │  Step 3: ElevenLabs   │
        │  Text-to-Speech       │
        │  ─────────────────    │
        │  Text → Audio         │
        └───────────────────────┘
                    ↓
Output: Audio Response (MP3)
```

---

## Component Details

### 1. Express Server (`server.js`)

**Responsibilities:**
- HTTP server with single endpoint
- File upload handling via multer
- Request validation
- Error handling and logging
- Response streaming

**Key Technologies:**
- Express.js for HTTP server
- Multer for multipart/form-data parsing
- In-memory storage for audio buffers

### 2. Speech-to-Text (Deepgram)

**Function:** `transcribeAudio(audioBuffer)`

**Input:** Audio buffer (any format)
**Output:** Transcribed text string

**Features:**
- Model: `nova-2` (latest, most accurate)
- Smart formatting enabled
- Supports multiple audio formats
- Error handling with step tracking

**Error Cases:**
- Invalid audio format
- Empty/silent audio
- API key issues
- Network failures

### 3. Language Model (Gemini)

**Function:** `getGeminiResponse(userMessage)`

**Input:** User's transcribed message
**Output:** Assistant's text response

**Configuration:**
- Model: `gemini-1.5-flash` (free tier)
- System instruction: Defines personality
- No streaming (simple completion)

**System Prompt:**
```
You are a helpful and friendly voice assistant. 
Keep your responses concise and conversational, 
as they will be spoken aloud. Aim for responses 
that are 2-3 sentences unless more detail is 
specifically requested.
```

**Error Cases:**
- API key issues
- Rate limits
- Invalid requests
- Network failures

### 4. Text-to-Speech (ElevenLabs)

**Function:** `textToSpeech(text)`

**Input:** Text to speak
**Output:** Audio buffer (MP3)

**Configuration:**
- Voice: Rachel (default, configurable)
- Model: `eleven_multilingual_v2`
- Stability: 0.5
- Similarity boost: 0.75

**Error Cases:**
- API key issues
- Character quota exceeded
- Invalid voice ID
- Network failures

---

## Data Flow

### Request Flow

```javascript
1. Client uploads audio file
   → Content-Type: multipart/form-data
   → Field name: "audio"
   → Stored in memory via multer

2. Audio → Deepgram
   → Buffer sent to Deepgram API
   → Receives JSON with transcript
   → Extracts text from response

3. Text → Gemini
   → Transcript sent with system prompt
   → Receives response text
   → Extracts text from response

4. Text → ElevenLabs
   → Response text sent to TTS API
   → Receives audio stream
   → Collects chunks into buffer

5. Audio → Client
   → Sets Content-Type: audio/mpeg
   → Streams buffer as response
   → Client plays audio
```

### Error Flow

```javascript
try {
  validateInput()      // → 400 Bad Request
  transcribeAudio()    // → 500 with step: "STT"
  getGeminiResponse()  // → 500 with step: "LLM"
  textToSpeech()       // → 500 with step: "TTS"
} catch (error) {
  return {
    error: "Internal server error",
    message: error.message,
    step: error.step  // Identifies which API failed
  }
}
```

---

## API Contracts

### POST /converse

**Request:**
```http
POST /converse HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="audio"; filename="recording.wav"
Content-Type: audio/wav

[binary audio data]
------WebKitFormBoundary--
```

**Success Response (200):**
```http
HTTP/1.1 200 OK
Content-Type: audio/mpeg
Content-Length: 67890

[binary audio data - MP3]
```

**Error Response (400):**
```json
{
  "error": "No audio file provided"
}
```

**Error Response (500):**
```json
{
  "error": "Internal server error",
  "message": "API key is invalid",
  "step": "STT (Deepgram)"
}
```

### GET /health

**Success Response (200):**
```json
{
  "status": "ok",
  "services": {
    "deepgram": true,
    "gemini": true,
    "elevenlabs": true
  }
}
```

---

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DEEPGRAM_API_KEY` | Yes | Deepgram API key | `abc123...` |
| `GEMINI_API_KEY` | Yes | Google Gemini API key | `AIza...` |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs API key | `xyz789...` |
| `ELEVENLABS_VOICE_ID` | No | Voice to use | `21m00Tcm4TlvDq8ikWAM` |
| `PORT` | No | Server port | `3000` |

### Default Values

- Port: `3000`
- Voice: Rachel (`21m00Tcm4TlvDq8ikWAM`)
- Model (STT): `nova-2`
- Model (LLM): `gemini-1.5-flash`
- Model (TTS): `eleven_multilingual_v2`

---

## Performance Characteristics

### Latency

| Step | Typical | Range |
|------|---------|-------|
| Upload | 50ms | 10-100ms |
| Deepgram STT | 2s | 1-3s |
| Gemini LLM | 3s | 2-5s |
| ElevenLabs TTS | 3s | 2-4s |
| Download | 100ms | 50-200ms |
| **Total** | **8s** | **5-12s** |

*Times vary based on audio length, response length, and network conditions*

### Throughput

- Concurrent requests supported (limited by API rate limits)
- No shared state between requests
- Stateless design allows horizontal scaling

### Resource Usage

- Memory: ~50MB base + ~1MB per concurrent request
- CPU: Minimal (I/O bound)
- Network: ~100KB in + ~200KB out per request

---

## Security Considerations

### Current Implementation

- ✅ No persistent storage (audio in memory only)
- ✅ API keys in environment variables
- ✅ Basic input validation
- ✅ Error messages don't leak sensitive info

### Not Implemented (Future)

- ❌ Authentication/authorization
- ❌ Rate limiting
- ❌ Request signing
- ❌ Audio file validation (format, size, duration)
- ❌ HTTPS enforcement
- ❌ API key rotation
- ❌ Audit logging

---

## Limitations

### By Design (Minimal MVP)

1. **No Memory:** Each request is independent
2. **No Streaming:** Full audio required upfront
3. **No Tools:** Claude used for text completion only
4. **No History:** Can't reference previous conversations
5. **No Authentication:** Open endpoint

### Technical Limitations

1. **Audio Size:** Limited by Deepgram (typically 250MB)
2. **Response Length:** Limited by Claude (1024 tokens)
3. **TTS Length:** Limited by ElevenLabs quota
4. **Concurrent Requests:** Limited by API rate limits

---

## Extension Points

### Easy Additions

1. **Conversation Memory:**
   ```javascript
   // Store conversation history per user
   const conversations = new Map();
   
   app.post('/converse', (req, res) => {
     const userId = req.headers['x-user-id'];
     const history = conversations.get(userId) || [];
     // Include history in Gemini request
   });
   ```

2. **Streaming Support:**
   ```javascript
   // Stream audio as it's generated
   deepgram.listen.live(audioStream)
     .pipe(claudeStream)
     .pipe(elevenlabsStream)
     .pipe(res);
   ```

3. **Tool Use:**
   ```javascript
   // Add tools to Gemini request
   const model = genAI.getGenerativeModel({
     model: 'gemini-1.5-flash',
     tools: [weatherTool, calculatorTool],
     // ...
   });
   ```

4. **Authentication:**
   ```javascript
   app.use('/converse', authenticateToken);
   ```

### Architectural Changes

1. **WebSocket:** Real-time bidirectional audio
2. **Queue System:** Background processing for long tasks
3. **Database:** Store conversations, user preferences
4. **Caching:** Cache TTS for common responses
5. **Load Balancer:** Distribute across multiple instances

---

## Testing Strategy

### Unit Tests
- Individual function testing
- Mock API responses
- Error handling validation

### Integration Tests
- Full pipeline end-to-end
- Real API calls (dev environment)
- Performance benchmarks

### Load Tests
- Concurrent request handling
- Rate limit behavior
- Resource usage under load

### Manual Tests
- Browser test page
- curl scripts
- Different audio formats

See `TESTING.md` for detailed testing procedures.
