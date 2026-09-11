# Environment Variables Reference

Complete guide to all environment variables used by the voice assistant backend.

## Quick Start

### Development (Local)
```bash
cp .env.example .env
# Edit .env with your local values
# Run: npm start
```

### Production (Render)
Set these in Render dashboard → Environment Variables:
- `DEEPGRAM_API_KEY` (required)
- `GEMINI_API_KEY` (required)
- `CHROMA_URL` (required)
- `CHROMA_API_KEY` (required)
- `OPENWEATHER_API_KEY` (optional, for weather tool)
- `SERPER_API_KEY` (optional, for web search tool)

---

## Detailed Variable Reference

### Core LLM & Transcription (Required)

#### `DEEPGRAM_API_KEY`
- **Purpose**: Speech-to-text transcription
- **Type**: String (API key)
- **Required**: Yes
- **Where to get**: https://console.deepgram.com/
- **How to get**:
  1. Sign up at https://console.deepgram.com
  2. Go to "API Keys"
  3. Click "Create API Key"
  4. Select "Scopes: Read" (for API key)
  5. Copy the key
- **Example**: `c94c49c55aff1bc3ea9b3f260c38f1849de18cec`
- **Notes**: 
  - Used for `/converse` endpoint (audio transcription)
  - Deepgram free tier includes 50,000 monthly API calls
  - Each 1-minute audio = ~1 API call

#### `GEMINI_API_KEY`
- **Purpose**: Large Language Model (LLM) for generating responses
- **Type**: String (API key)
- **Required**: Yes (if `LLM_PROVIDER=gemini` or `LLM_PROVIDER=cloud`)
- **Where to get**: https://aistudio.google.com/app/apikeys
- **How to get**:
  1. Go to https://aistudio.google.com/app/apikeys
  2. Click "Get API Key"
  3. Select or create a Google Cloud project
  4. Click "Create API key"
  5. Copy the key
- **Example**: `AIzaSyB_example_key_here`
- **Notes**:
  - Free tier: 60 requests per minute, 1500 requests per day
  - Model used: `gemini-3.6-flash` (latest, fastest)
  - Supports function calling for tools
  - In production, Ollama is NOT used (only Gemini)

---

### Memory & Vector Database (Required)

#### `CHROMA_URL`
- **Purpose**: URL for Chroma vector database (memory persistence)
- **Type**: String (URL)
- **Required**: Yes
- **Development value**: `http://localhost:8000`
- **Production value**: `https://api.trychroma.com` (or your Chroma Cloud URL)
- **How to set up for production**:
  1. Sign up at https://www.trychroma.com
  2. Create a new project
  3. Find the URL in "API Settings" or "Connection"
  4. Use that URL here
- **Notes**:
  - Local development: Start Chroma with `docker run -p 8000:8000 chromadb/chroma`
  - Production: Use Chroma Cloud (hosted, no setup needed)
  - If not set, memory features are disabled (graceful degradation)

#### `CHROMA_API_KEY`
- **Purpose**: Authentication token for Chroma Cloud
- **Type**: String (API key)
- **Required**: Only if using Chroma Cloud (production)
- **Leave empty for**: Local Chroma server development
- **How to get**:
  1. Go to your Chroma Cloud project dashboard
  2. Find "API Settings" or "Credentials"
  3. Copy the API key / Authentication Token
- **Example**: `chr_live_abc123xyz789`
- **Notes**:
  - Used only with `CHROMA_URL=https://api.trychroma.com` or similar
  - Local Chroma doesn't need authentication
  - Regenerate if compromised

---

### LLM Provider Configuration (Optional but Recommended)

#### `LLM_PROVIDER`
- **Purpose**: Choose which LLM to use
- **Type**: String
- **Valid values**:
  - `local` - Use Ollama (local, fast, free, requires setup)
  - `gemini` - Use Google Gemini (cloud, production-ready)
  - `cloud` - Alias for `gemini` (legacy, maps to gemini)
- **Default**: `local`
- **Development**: Use `local` with Ollama
- **Production**: Must be `gemini` (Ollama not available on Render)
- **Example**: `gemini`
- **Notes**:
  - When set to `gemini`, Ollama is completely skipped (no timeout delays)
  - Code checks `normalizedProvider` which maps `cloud` → `gemini`

#### `NODE_ENV`
- **Purpose**: Node.js environment mode
- **Type**: String
- **Valid values**: `development`, `production`
- **Default**: Not set (no special behavior)
- **Production value**: `production`
- **Notes**: Automatically set in Dockerfile

#### `EMBEDDING_MODEL`
- **Purpose**: Model for generating text embeddings (for memory retrieval)
- **Type**: String
- **Valid values**:
  - `mxbai-embed-large` (recommended, 1024-dim, good quality)
  - `nomic-embed-text` (lighter, 768-dim)
  - Any Ollama embedding model
- **Default**: `mxbai-embed-large`
- **Production**: Keep as `mxbai-embed-large`
- **Notes**:
  - Used to embed user messages before storing/retrieving memories
  - Must be available in Ollama (local) or Chroma Cloud (production)
  - Embedding happens server-side automatically

---

### Tool API Keys (Optional)

Tools are optional integrations that extend functionality. Skip if not needed.

#### `OPENWEATHER_API_KEY`
- **Purpose**: Get current weather for a location
- **Type**: String (API key)
- **Required**: No (weather tool is optional)
- **Where to get**: https://openweathermap.org/api
- **How to get**:
  1. Sign up at https://openweathermap.org
  2. Go to "API Keys" tab
  3. Copy your default API key
- **Example**: `12efd095161f87817aa6af3b56e54f05`
- **Trigger**: User asks "What's the weather in London?"
- **Notes**:
  - Free tier: 1000 API calls per day
  - If not set, tool returns mock weather data
  - See `/get_weather` in tools.js for implementation

#### `SERPER_API_KEY`
- **Purpose**: Web search for current information
- **Type**: String (API key)
- **Required**: No (web search tool is optional)
- **Where to get**: https://serper.dev
- **How to get**:
  1. Go to https://serper.dev
  2. Sign up with email
  3. Go to API dashboard
  4. Copy your API key
- **Example**: `b2891beeb2eca7db70cbe31f768b1f9b7dda28a4`
- **Trigger**: User asks "What's the latest news?"
- **Notes**:
  - Free tier: Includes free credits
  - If not set, tool returns mock search results
  - See `/web_search` in tools.js for implementation

#### `GOOGLE_CALENDAR_CLIENT_ID`
- **Purpose**: Create calendar events (not currently implemented)
- **Type**: String (OAuth client ID)
- **Required**: No
- **Status**: Placeholder for future calendar integration
- **Notes**: Requires full OAuth2 flow to implement

#### `GOOGLE_CALENDAR_CLIENT_SECRET`
- **Purpose**: Google Calendar authentication secret
- **Type**: String (secret)
- **Required**: No
- **Status**: Placeholder for future calendar integration

#### `GOOGLE_CALENDAR_REFRESH_TOKEN`
- **Purpose**: Long-lived Google Calendar token
- **Type**: String (token)
- **Required**: No
- **Status**: Placeholder for future calendar integration

---

### Ollama Configuration (Development Only)

These are only used when `LLM_PROVIDER=local`.

#### `OLLAMA_BASE_URL`
- **Purpose**: URL where Ollama server is running
- **Type**: String (URL)
- **Default**: `http://localhost:11434`
- **Production**: Not used (only for development)
- **How to set up**:
  1. Install Ollama: https://ollama.ai
  2. Run: `ollama serve`
  3. In another terminal: `ollama pull qwen2.5:7b-instruct`
- **Notes**:
  - Only needed for local development
  - Ignored when `LLM_PROVIDER=gemini`
  - Port 11434 is Ollama default

#### `OLLAMA_MODEL`
- **Purpose**: Which Ollama model to use for chat
- **Type**: String
- **Valid values**: Any Ollama model (e.g., `llama2`, `qwen2.5:7b-instruct`)
- **Default**: `llama3.2`
- **Recommended**: `qwen2.5:7b-instruct` (better tool support)
- **Production**: Not used (only for development)
- **Notes**:
  - Model must be downloaded first: `ollama pull model-name`
  - Custom fine-tuned models can be used: `ollama pull my-assistant`
  - Tool calling requires compatible model

---

### Server Configuration (Automatic)

These are set automatically and rarely need changing.

#### `PORT`
- **Purpose**: HTTP port the server listens on
- **Type**: Integer
- **Default**: `3000`
- **Production**: `3000` (Render exposes this via public URL)
- **Notes**: Render automatically forwards external traffic to this port

#### `TOOLS_ENABLED`
- **Purpose**: Enable/disable function calling (tool use)
- **Type**: Boolean string (`"true"` or `"false"`)
- **Default**: `"true"` (enabled)
- **Production**: Keep as `"true"`
- **Notes**:
  - When `true`: Model can call tools (get_weather, web_search)
  - When `false`: Simple chat-only mode (no tool calls)
  - Ollama models must support tools if enabled

---

## Environment Variable Checklist

### For Local Development
- [ ] `DEEPGRAM_API_KEY` - Required
- [ ] `GEMINI_API_KEY` - Required
- [ ] `CHROMA_URL=http://localhost:8000` - Optional (defaults to this)
- [ ] `LLM_PROVIDER=local` - Optional (defaults to this)
- [ ] `OLLAMA_MODEL=qwen2.5:7b-instruct` - Optional
- [ ] `OPENWEATHER_API_KEY` - Optional (for weather tool)
- [ ] `SERPER_API_KEY` - Optional (for search tool)

### For Production (Render)
- [ ] `DEEPGRAM_API_KEY` - **Required**
- [ ] `GEMINI_API_KEY` - **Required**
- [ ] `LLM_PROVIDER=gemini` - **Required** (set in Dockerfile)
- [ ] `CHROMA_URL=https://api.trychroma.com` - **Required**
- [ ] `CHROMA_API_KEY` - **Required**
- [ ] `OPENWEATHER_API_KEY` - Optional
- [ ] `SERPER_API_KEY` - Optional
- [ ] `NODE_ENV=production` - Set in Dockerfile
- [ ] `EMBEDDING_MODEL=mxbai-embed-large` - Set in render.yaml

---

## How to Set Environment Variables

### Local Development
1. Copy `.env.example` to `.env`
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values
   ```bash
   nano .env
   # or
   vim .env
   ```

3. Start server (reads `.env` automatically)
   ```bash
   npm start
   ```

### Production (Render Dashboard)
1. Go to https://dashboard.render.com
2. Select your service
3. Go to "Environment" tab
4. Click "Add Environment Variable"
5. Enter key and value
6. Click "Add"
7. Service auto-redeploys when you save

### Production (render.yaml)
Environment variables marked `sync: false` must be set manually in Render dashboard.
Variables with `value: ...` are set automatically.

---

## Security Best Practices

### Do's ✅
- Use strong, unique API keys
- Store `.env` files locally only (never commit to git)
- Rotate API keys every 90 days
- Use Render's environment variables (not hardcoded)
- Monitor API usage (Deepgram, Gemini dashboards)
- Enable billing alerts

### Don'ts ❌
- Never commit `.env` to GitHub
- Never share API keys in chat/emails
- Never use API keys directly in code
- Never use same key across multiple services
- Never hardcode secrets in Dockerfile

### Verify .gitignore
```bash
cat .gitignore | grep "^\.env"
# Should show: .env
```

---

## Troubleshooting

### "Error: Deepgram API key not configured"
- **Cause**: `DEEPGRAM_API_KEY` not set
- **Fix**: 
  - Development: Add to `.env`
  - Production: Add to Render Environment Variables

### "Error: Chroma server not reachable"
- **Cause**: `CHROMA_URL` wrong or local Chroma not running
- **Fix**:
  - Local: Start Chroma: `docker run -p 8000:8000 chromadb/chroma`
  - Production: Verify `CHROMA_URL=https://api.trychroma.com`

### "Error: Ollama model unavailable"
- **Cause**: Model not downloaded or `OLLAMA_BASE_URL` wrong
- **Fix**:
  - Download model: `ollama pull qwen2.5:7b-instruct`
  - Verify Ollama running: `ollama serve`
  - (Note: Only needed for `LLM_PROVIDER=local`)

### "Error: Unknown provider"
- **Cause**: `LLM_PROVIDER` set to invalid value
- **Fix**: Must be `local`, `gemini`, or `cloud`

### `/health shows "degraded"`
- Check which service is failing
- Set missing API keys in environment
- Restart service

---

## Environment Variable Priority

If multiple sources define the same variable:
1. **Runtime environment** (Render dashboard) - Highest priority
2. **`.env` file** (local) - Used if not in environment
3. **Defaults in code** - Fallback if not set anywhere

Example:
```bash
# If CHROMA_URL is not set anywhere, code uses: http://localhost:8000
# But Render env var overrides this
# And .env file is used when running locally
```

---

## Reference Tables

### By Priority (What to Set First)
| Priority | Variable | Impact if Missing |
|----------|----------|-------------------|
| Critical | DEEPGRAM_API_KEY | STT fails completely |
| Critical | GEMINI_API_KEY | LLM responses fail |
| Critical | CHROMA_URL | Memory disabled gracefully |
| Critical | CHROMA_API_KEY | (only prod) Memory fails |
| High | LLM_PROVIDER | Wrong LLM used, timeout delays |
| Medium | OPENWEATHER_API_KEY | Weather returns mock data |
| Medium | SERPER_API_KEY | Search returns mock data |
| Low | EMBEDDING_MODEL | Uses default (usually fine) |

### By Environment
| Development | Production |
|-------------|-----------|
| LLM_PROVIDER=local | LLM_PROVIDER=gemini |
| OLLAMA_MODEL=... | (not used) |
| CHROMA_URL=http://localhost:8000 | CHROMA_URL=https://api.trychroma.com |
| (no CHROMA_API_KEY) | CHROMA_API_KEY=... |
| NODE_ENV not set | NODE_ENV=production |

---

## Quick Reference

```bash
# Minimal working setup (local)
DEEPGRAM_API_KEY=your_key
GEMINI_API_KEY=your_key
LLM_PROVIDER=local
OLLAMA_MODEL=qwen2.5:7b-instruct

# Minimal working setup (production)
DEEPGRAM_API_KEY=your_key
GEMINI_API_KEY=your_key
CHROMA_URL=https://api.trychroma.com
CHROMA_API_KEY=your_key
LLM_PROVIDER=gemini
```
