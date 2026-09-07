# Quick Start: my-assistant Integration

## TL;DR - What Changed

✅ **LLM**: Now uses your fine-tuned `my-assistant` model (was: qwen2.5)
✅ **Tools**: Disabled for simple chat (was: enabled with function calling)
✅ **Health Check**: Now verifies Ollama + model availability
✅ **Error Messages**: Clear feedback when Ollama is down
✅ **Future-Ready**: Tool code preserved, can re-enable with one env var

---

## Start Your Server

### 1. Restart to pick up changes
```bash
cd ~/agent

# Stop current server (if running)
pkill -f "node server.js"

# Start fresh
npm start
```

**Expected output:**
```
[LLM] Provider: local (my-assistant)
[LLM] Tools enabled: false
[Embedding] Provider: ollama, Model: mxbai-embed-large
[Memory] Chroma initialized successfully
🎤 Voice Assistant Backend running on port 3000
```

✅ **Key indicators:**
- Provider: local (my-assistant) ← Your model!
- Tools enabled: false ← Simple chat mode

---

## Test 1: Health Check (30 seconds)

```bash
curl http://localhost:3000/health | jq .
```

### ✅ Healthy Response
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
        "..."
      ]
    }
  }
}
```

**What this means:**
- ✅ All services operational
- ✅ Your fine-tuned model is loaded
- ✅ Tools disabled (as configured)

---

### ❌ Unhealthy Response

**If Ollama is down:**
```json
{
  "status": "degraded",
  "services": {
    "ollama": {
      "reachable": false,
      "model_available": false,
      "error": "Cannot reach Ollama: fetch failed"
    }
  }
}
```

**Fix:** `ollama serve`

**If model not found:**
```json
{
  "status": "degraded",
  "services": {
    "ollama": {
      "reachable": true,
      "model_available": false,
      "error": "Model \"my-assistant\" not found. Available: ..."
    }
  }
}
```

**Fix:** Verify `ollama list` shows your model

---

## Test 2: Voice Conversation (2 minutes)

### Using existing test audio:
```bash
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" \
  -F "sessionId=my-first-test" \
  -o response.wav

# Play response
afplay response.wav
```

### Watch server logs:
```
[Memory] Using session ID: my-first-test
[1/7] Received audio file: 123456 bytes
[2/7] Transcribed: "Hello, how are you?"
[3/7] Retrieving relevant memories...
[4/7] Assistant response: "I'm doing well, thank you!"
[5/7] Extracting durable memory...
[6/7] Generating speech...
[7/7] Generated audio: 234567 bytes
```

**✅ Success indicators:**
- All 7 steps complete
- No errors
- No `[Tools]` logs (tools disabled)
- Response audio generated

---

## Test 3: Web Interface (1 minute)

```bash
open http://localhost:3000
```

1. Click **"Record"**
2. Say: *"Hello, how are you today?"*
3. Click **"Stop"**
4. Wait for response to play

**Your fine-tuned model should respond!**

---

## Verify Your Fine-Tuning

Test with prompts from your training data to see the LoRA fine-tuning in action:

**Example task-confirmation style prompts:**
- "Can you help me schedule a meeting?"
- "I need to update my calendar"
- "Let's create a reminder"

**Your model should respond in its trained style!**

---

## Compare with Cloud LLM (Optional)

Want to compare your model with Gemini?

### Switch to cloud:
```bash
# Edit .env
echo "LLM_PROVIDER=cloud" > .env.temp
cat .env | grep -v LLM_PROVIDER >> .env.temp
mv .env.temp .env

# Restart
npm start
```

**Test same query:**
```bash
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" \
  -F "sessionId=cloud-test" \
  -o response-cloud.wav

afplay response-cloud.wav
```

### Switch back to local:
```bash
# Edit .env
sed -i '' 's/LLM_PROVIDER=cloud/LLM_PROVIDER=local/' .env

# Restart
npm start
```

---

## Troubleshooting

### Error: "Local model unavailable"

**Request returns:**
```json
{
  "error": "Internal server error",
  "message": "Local model unavailable — is Ollama running?",
  "step": "LLM (Ollama)"
}
```

**Fix:**
```bash
ollama serve
```

---

### Error: Model not found

**Health check shows model not available**

**Fix:**
```bash
# Check if model exists
ollama list | grep my-assistant

# If not found, verify your Modelfile and create:
ollama create my-assistant -f Modelfile
```

---

### Server won't start

**Error during startup:**
```
[Memory] Failed to initialize Chroma
```

**Fix:**
```bash
# Start Chroma
docker start chroma-server

# Or create if doesn't exist:
docker run -d --name chroma-server -p 8000:8000 \
  -v ~/agent/data/chroma:/chroma/chroma \
  chromadb/chroma:latest
```

---

## Re-enable Tools Later

When you have a tool-capable model:

### 1. Update .env:
```bash
OLLAMA_MODEL=my-assistant-with-tools
TOOLS_ENABLED=true
```

### 2. Restart:
```bash
npm start
```

### 3. Verify in logs:
```
[LLM] Tools enabled: true
```

### 4. Test tool usage:
Say: *"What's the weather in San Francisco?"*

**Expected logs:**
```
[Tools] Model requested 1 tool call(s)
[Tools] Calling: get_weather
[Tool] Executing: get_weather
[Tools] Result: success
```

---

## Reference Documents

- **MY_ASSISTANT_INTEGRATION.md** - Complete integration overview
- **TEST_MY_ASSISTANT.md** - Detailed testing guide with all scenarios
- **verify-my-assistant.sh** - Automated verification script

---

## Quick Commands

```bash
# Restart server
pkill -f "node server.js" && npm start

# Check health
curl http://localhost:3000/health | jq .

# Test conversation
curl -X POST http://localhost:3000/converse \
  -F "audio=@test.wav" -o response.wav && afplay response.wav

# Verify configuration
./verify-my-assistant.sh

# Check Ollama
ollama list | grep my-assistant

# Check Chroma
docker ps | grep chroma-server
```

---

## Success Checklist

Before testing, verify:

- [ ] Server restarted with new code
- [ ] Health check shows `status: "ok"`
- [ ] `ollama.model_available: true`
- [ ] `tools_enabled: false`
- [ ] Logs show: `Provider: local (my-assistant)`

During testing:

- [ ] Audio requests return WAV responses
- [ ] Logs show all 7 steps completing
- [ ] No `[Tools]` logs appear
- [ ] Responses match your fine-tuned style

---

**Your fine-tuned model is ready!** 🎉

Start the server and test with your task-confirmation prompts to see the LoRA fine-tuning in action.
