# Testing Guide: my-assistant Model Integration

## Configuration Changes Made

✅ **Updated Configuration:**
- `OLLAMA_MODEL=my-assistant` in .env
- `TOOLS_ENABLED=false` (simple chat mode, no function calling)
- Tool-calling code preserved but gated behind TOOLS_ENABLED flag
- Enhanced health check with Ollama connectivity + model verification

## How to Test

### Prerequisites

**1. Ensure Ollama is running:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
```

**2. Verify your model is loaded:**
```bash
# List available models
ollama list

# Should see "my-assistant" in the list
# If not, ensure your model is properly set up:
ollama show my-assistant
```

**3. Ensure Chroma is running:**
```bash
# Check if Chroma container exists
docker ps -a | grep chroma-server

# If not running, start it:
docker start chroma-server

# Or create it if it doesn't exist:
docker run -d \
  --name chroma-server \
  -p 8000:8000 \
  -v ~/agent/data/chroma:/chroma/chroma \
  chromadb/chroma:latest
```

---

## Test 1: Health Check

### Expected: Healthy Response

```bash
curl http://localhost:3000/health | jq .
```

**Healthy output:**
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
      "model_available": true,
      "model_name": "my-assistant",
      "tools_enabled": false,
      "available_models": [
        "my-assistant:latest",
        "qwen2.5:7b-instruct",
        "llama3.2:latest",
        "..."
      ]
    }
  }
}
```

**Interpretation:**
- ✅ `status: "ok"` - All critical services working
- ✅ `ollama.reachable: true` - Ollama is running
- ✅ `ollama.model_available: true` - Your model is loaded
- ✅ `tools_enabled: false` - Simple chat mode (no function calling)

---

### Expected: Unhealthy Responses

**Scenario 1: Ollama not running**
```json
{
  "status": "degraded",
  "services": {
    "deepgram": true,
    "gemini": true,
    "piper": true,
    "chroma": true,
    "ollama": {
      "reachable": false,
      "model_available": false,
      "model_name": "my-assistant",
      "tools_enabled": false,
      "error": "Cannot reach Ollama: fetch failed"
    }
  }
}
```

**Fix:** Start Ollama with `ollama serve`

---

**Scenario 2: Model not found**
```json
{
  "status": "degraded",
  "services": {
    "deepgram": true,
    "gemini": true,
    "piper": true,
    "chroma": true,
    "ollama": {
      "reachable": true,
      "model_available": false,
      "model_name": "my-assistant",
      "tools_enabled": false,
      "available_models": [
        "qwen2.5:7b-instruct",
        "llama3.2:latest"
      ],
      "error": "Model \"my-assistant\" not found. Available: qwen2.5:7b-instruct, llama3.2:latest"
    }
  }
}
```

**Fix:** Ensure your model is properly created in Ollama:
```bash
# Check if model exists
ollama list | grep my-assistant

# If not, verify your Modelfile and create it:
ollama create my-assistant -f ./Modelfile
```

---

**Scenario 3: Chroma not running**
```json
{
  "status": "degraded",
  "services": {
    "deepgram": true,
    "gemini": true,
    "piper": true,
    "chroma": false,
    "ollama": {
      "reachable": true,
      "model_available": true,
      "model_name": "my-assistant",
      "tools_enabled": false
    }
  }
}
```

**Fix:** Start Chroma with `docker start chroma-server`

---

## Test 2: Voice Conversation Test

### Step 1: Start the server

```bash
cd ~/agent
npm start
```

**Expected output:**
```
[LLM] Provider: local (my-assistant)
[LLM] Tools enabled: false
[Embedding] Provider: ollama, Model: mxbai-embed-large
[Memory] Chroma initialized successfully
🎤 Voice Assistant Backend running on port 3000

📍 Endpoints:
   GET  /          - Test page (open in browser)
   POST /converse  - Voice API (send audio, receive audio)
   GET  /health    - Service status
```

**Key indicators:**
- ✅ `[LLM] Provider: local (my-assistant)` - Using your model
- ✅ `[LLM] Tools enabled: false` - Simple chat mode
- ✅ `[Memory] Chroma initialized successfully` - Memory working

---

### Step 2: Test with audio file

**Option A: Use existing test file**
```bash
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" \
  -F "sessionId=test-session-1" \
  -o response.wav

# Play the response (macOS)
afplay response.wav
```

**Option B: Record new audio**
```bash
# Record 5 seconds of audio on macOS
# Say something like: "Hello, how are you today?"
rec -r 16000 -c 1 -b 16 question.wav trim 0 5

# Send to server
curl -X POST http://localhost:3000/converse \
  -F "audio=@question.wav" \
  -F "sessionId=test-session-2" \
  -o response.wav

# Play response
afplay response.wav
```

---

### Step 3: Monitor server logs

**Successful request logs:**
```
[Memory] Using session ID: test-session-1
[1/7] Received audio file: 123456 bytes
[2/7] Transcribed: "Hello, how are you today?"
[3/7] Retrieving relevant memories...
[Memory] Session: test-session-1 - No memories found
[4/7] Assistant response: "I'm doing well, thank you for asking! How can I help you today?"
[5/7] Extracting durable memory...
[6/7] Generating speech...
[7/7] Generated audio: 234567 bytes
```

**Key indicators:**
- ✅ Step 2: Deepgram transcription working
- ✅ Step 3: Memory retrieval working (empty is OK for first request)
- ✅ Step 4: Your model generated a response
- ✅ Step 7: Piper TTS generated audio

**No tool-calling logs** (like `[Tools] Model requested...`) because TOOLS_ENABLED=false

---

### Step 4: Test conversation memory (multiple turns)

```bash
# Turn 1: Introduce yourself
curl -X POST http://localhost:3000/converse \
  -F "audio=@turn1.wav" \
  -F "sessionId=memory-test" \
  -o response1.wav

# Turn 2: Ask a follow-up (same session)
curl -X POST http://localhost:3000/converse \
  -F "audio=@turn2.wav" \
  -F "sessionId=memory-test" \
  -o response2.wav

# Turn 3: Reference earlier conversation
curl -X POST http://localhost:3000/converse \
  -F "audio=@turn3.wav" \
  -F "sessionId=memory-test" \
  -o response3.wav
```

**Expected behavior:**
- Server remembers context across turns (within same session)
- Relevant memories retrieved from Chroma
- Responses are contextually aware

**Server logs show:**
```
[Memory] Session: memory-test - Retrieved: 2 memories
[Memory] Extracted durable fact: "User prefers concise answers"
[Memory] Stored memory: mem_xyz for session memory-test
```

---

## Test 3: Error Handling

### Test A: Ollama down

```bash
# Stop Ollama
pkill ollama

# Try to make request
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" \
  -F "sessionId=error-test" \
  -o response.wav
```

**Expected error response:**
```json
{
  "error": "Internal server error",
  "message": "Local model unavailable — is Ollama running? (try: ollama serve)",
  "step": "LLM (Ollama)"
}
```

**Server logs:**
```
[LLM] Ollama error: Local model unavailable — is Ollama running? (try: ollama serve)
Error in /converse: Error: Local model unavailable — is Ollama running? (try: ollama serve)
```

**Fix:** `ollama serve`

---

### Test B: Wrong model name

```bash
# Change model in .env to non-existent model
echo "OLLAMA_MODEL=wrong-model-name" >> .env

# Restart server
npm start

# Try request
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" \
  -F "sessionId=error-test-2" \
  -o response.wav
```

**Expected error:**
```json
{
  "error": "Internal server error",
  "message": "Ollama API error: Not Found",
  "step": "LLM (Ollama)"
}
```

**Fix:** Correct OLLAMA_MODEL in .env to `my-assistant`

---

### Test C: Invalid audio file

```bash
# Send a text file instead of audio
echo "not audio" > fake.wav

curl -X POST http://localhost:3000/converse \
  -F "audio=@fake.wav" \
  -F "sessionId=error-test-3" \
  -o response.wav
```

**Expected error:**
```json
{
  "error": "Internal server error",
  "message": "Deepgram error: ...",
  "step": "STT (Deepgram)"
}
```

**Interpretation:** Deepgram rejected invalid audio

---

## Test 4: Compare with Cloud LLM (Gemini)

To verify your fine-tuned model's quality:

```bash
# Test with your model
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" \
  -F "sessionId=compare-local" \
  -o response-local.wav

# Switch to Gemini
echo "LLM_PROVIDER=cloud" >> .env
npm start

# Same test with Gemini
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" \
  -F "sessionId=compare-cloud" \
  -o response-cloud.wav

# Compare responses
afplay response-local.wav
afplay response-cloud.wav
```

**Server logs show different LLM:**
```
# Local:
[LLM] Provider: local (my-assistant)

# Cloud:
[LLM] Provider: cloud (Gemini)
```

---

## Test 5: Web Interface Test

**Open in browser:**
```bash
open http://localhost:3000
```

1. Click "Record" button
2. Speak a question (e.g., "What's the weather like?")
3. Click "Stop"
4. Wait for response audio to play automatically

**Browser console shows:**
```
Recording started
Stopped recording, audio size: 123456 bytes
Sending audio to server...
Response received, audio size: 234567 bytes
Playing response audio
```

---

## Expected Behavior Summary

### ✅ Healthy System

| Component | Status | Indicator |
|-----------|--------|-----------|
| **Deepgram STT** | ✅ Working | Transcripts appear in logs |
| **Ollama (my-assistant)** | ✅ Working | Responses generated, no tool calls |
| **Chroma Memory** | ✅ Working | Memories retrieved/stored |
| **Piper TTS** | ✅ Working | WAV audio returned |
| **Tool Calling** | ⏸️ Disabled | No `[Tools]` logs |

**Health check:** `status: "ok"`, all services true

**Logs:** Clean pipeline flow through all 7 steps

**Response time:** ~3-8 seconds (STT ~1s, LLM ~1-4s, TTS ~1-3s)

---

### ❌ Common Issues & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Ollama not running** | "Local model unavailable" | `ollama serve` |
| **Model not found** | "Model not found" in health check | `ollama list`, verify model exists |
| **Chroma down** | "Failed to initialize Chroma" | `docker start chroma-server` |
| **Wrong model name** | "Not Found" error | Fix OLLAMA_MODEL in .env |
| **API key missing** | Deepgram errors | Add DEEPGRAM_API_KEY to .env |
| **Audio format wrong** | Deepgram transcription fails | Use WAV 16kHz mono 16-bit |

---

## Re-enabling Tools Later

When you have a tool-capable model:

1. **Update .env:**
   ```bash
   OLLAMA_MODEL=my-assistant-with-tools
   TOOLS_ENABLED=true
   ```

2. **Restart server:**
   ```bash
   npm start
   ```

3. **Verify in logs:**
   ```
   [LLM] Tools enabled: true
   ```

4. **Test tool usage:**
   ```bash
   # Record: "What's the weather in San Francisco?"
   curl -X POST http://localhost:3000/converse \
     -F "audio=@weather-query.wav" \
     -F "sessionId=tools-test" \
     -o response.wav
   ```

5. **Watch for tool logs:**
   ```
   [Tools] Model requested 1 tool call(s)
   [Tools] Calling: get_weather
   [Tool] Executing: get_weather {"location": "San Francisco, CA"}
   [Tools] Result: success
   ```

---

## Quick Start Commands

```bash
# 1. Start all services
ollama serve &
docker start chroma-server

# 2. Verify health
curl http://localhost:3000/health | jq .

# 3. Start server
cd ~/agent
npm start

# 4. Test conversation
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" \
  -F "sessionId=quickstart" \
  -o response.wav && afplay response.wav

# 5. Check logs for successful pipeline
# Should see: [1/7] through [7/7] with no errors
```

---

## Success Criteria

✅ Health check shows `status: "ok"`
✅ `ollama.reachable: true` and `ollama.model_available: true`
✅ Audio request returns WAV response
✅ Server logs show clean 7-step pipeline
✅ No `[Tools]` logs (tools disabled)
✅ Responses sound natural from your fine-tuned model

**Your fine-tuned model is now integrated!** 🎉

Test it with your task-confirmation style prompts to see your LoRA fine-tuning in action.
