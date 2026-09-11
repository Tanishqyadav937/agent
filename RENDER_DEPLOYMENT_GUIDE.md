# Render Deployment Guide

## Overview
This guide walks you through deploying the voice assistant backend to Render with Docker, Gemini LLM, and Chroma Cloud memory.

## Prerequisites
Before deploying, ensure you have:

1. **Render Account** - Sign up at https://render.com
2. **GitHub Repository** - Code must be in a GitHub repo (connected to your Render account)
3. **API Keys** - Get these before deployment:
   - Deepgram: https://console.deepgram.com
   - Google Gemini: https://aistudio.google.com/app/apikeys
   - Chroma Cloud: https://www.trychroma.com (after signup)

## Step 1: Prepare Your Repository

### 1.1 Commit all deployment files
```bash
git add Dockerfile .dockerignore render.yaml .env.example
git commit -m "Add production deployment config for Render"
git push origin main
```

### 1.2 Verify files are in repo
```bash
git ls-files | grep -E "(Dockerfile|render.yaml|server.js|tools.js)"
```

## Step 2: Create Render Web Service

### Option A: Using render.yaml (Recommended)
```bash
# render.yaml is in the root of your repo
# Render will auto-detect it
# Go to https://render.com and connect your GitHub repo
# Render will prompt you to deploy the configuration
```

### Option B: Manual Render Dashboard Setup

1. Go to https://dashboard.render.com
2. Click "New" → "Web Service"
3. Select your GitHub repository
4. Fill in the form:
   - **Name**: `voice-assistant-api`
   - **Environment**: `Docker`
   - **Region**: `Oregon` (or closest to you)
   - **Branch**: `main`
   - **Build Command**: Leave empty (uses Dockerfile)
   - **Start Command**: Leave empty (uses Dockerfile CMD)

5. Click "Create Web Service"

## Step 3: Set Environment Variables

In the Render dashboard for your service:

### 3.1 Go to Environment tab

1. Click on your service name
2. Go to "Environment" section
3. Add each variable (see below)

### 3.2 Add Required Variables

| Variable | Value | Where to get |
|----------|-------|--------------|
| `DEEPGRAM_API_KEY` | Your API key | https://console.deepgram.com |
| `GEMINI_API_KEY` | Your API key | https://aistudio.google.com/app/apikeys |
| `CHROMA_URL` | `https://api.trychroma.com` | Your Chroma Cloud project |
| `CHROMA_API_KEY` | Your API key | Your Chroma Cloud dashboard |
| `OPENWEATHER_API_KEY` | (optional) | https://openweathermap.org/api |
| `SERPER_API_KEY` | (optional) | https://serper.dev |

### 3.3 Set Automatic Variables

These are already set in render.yaml, but verify:
```
NODE_ENV=production
LLM_PROVIDER=gemini
PORT=3000
EMBEDDING_MODEL=mxbai-embed-large
TOOLS_ENABLED=true
```

## Step 4: Deploy

### 4.1 Trigger deployment

If using render.yaml:
- Render auto-detects and deploys when you push

If manual:
- Click "Deploy" or push to GitHub (if autoDeploy enabled)

### 4.2 Monitor deployment

1. Watch logs in Render dashboard
2. Look for messages like:
   ```
   🎤 Voice Assistant Backend running on port 3000
   ```
3. Deployment typically takes 5-10 minutes

## Step 5: Verify Deployment

### 5.1 Get your service URL

In Render dashboard, find the URL (format: `https://voice-assistant-api.onrender.com`)

### 5.2 Test health endpoint

```bash
curl https://your-service-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "deepgram": true,
    "gemini": true,
    "piper": true,
    "chroma": true,
    "ollama": {
      "reachable": false,
      "model_available": false,
      "note": "Production mode: Ollama not used"
    }
  }
}
```

### 5.3 Test voice endpoint

```bash
curl -X POST https://your-service-url/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "render_test",
    "user_input": "Hello, tell me a joke"
  }'
```

Expected: JSON response with text + base64 audio

### 5.4 Test memory persistence

```bash
# First message - store memory
curl -X POST https://your-service-url/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "memory_test",
    "user_input": "My name is Alice and I work as an engineer"
  }'

# Second message - retrieve memory
curl -X POST https://your-service-url/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "memory_test",
    "user_input": "What is my profession?"
  }'

# Should include "engineer" or similar in response
```

## Troubleshooting

### Deployment fails with "Permission denied"
- **Cause**: Dockerfile references files not in repo
- **Fix**: Ensure all files (server.js, tools.js, avatar.html) are committed to git

### "Ollama not found" error
- **Cause**: LLM_PROVIDER still set to 'local'
- **Fix**: Verify `LLM_PROVIDER=gemini` in environment variables

### "Chroma API error: 401 Unauthorized"
- **Cause**: Invalid or missing CHROMA_API_KEY
- **Fix**: 
  - Verify key is correct in Render dashboard
  - Regenerate key in Chroma Cloud if needed
  - Restart service after updating

### "/health reports status: degraded"
- Check individual service statuses
- Most common: Missing API key (Deepgram, Gemini, or Chroma)
- Verify all three are set in environment

### Deployment timeout (>30 minutes)
- **Cause**: Dockerfile build too slow (building Piper from source)
- **Fix**: 
  - Check Render logs for build progress
  - Consider using pre-built Piper binary instead
  - Increase Render instance size

### Service crashes immediately after deploy
- Check "Logs" tab in Render dashboard
- Look for error in first few lines
- Common: Missing API key or CHROMA_URL not reachable

## Performance Tuning

### Instance Size
- **Starter** ($7/mo): Good for testing, ~1000 monthly active sessions
- **Standard** ($12/mo): Production, ~5000 monthly active sessions
- **Pro** ($49/mo): High traffic, auto-scaling available

### Build Optimization
The Docker build takes ~5 minutes because:
1. Python 3.11 runtime installation
2. Building Piper TTS from source
3. Downloading en_US-lessac-medium voice model

This is acceptable for production. If faster builds needed, consider:
- Pre-building Docker image and pushing to registry
- Using a lighter embedding model

## Monitoring

### Set up alerts (optional)
1. Go to service settings
2. Scroll to "Notifications"
3. Add email alerts for deployment failures

### View logs
```bash
# Via Render dashboard - "Logs" tab
# Or use Render CLI (if installed):
render logs voice-assistant-api
```

## Next Steps

1. **Configure alerting** if this is production
2. **Set up custom domain** (optional, in service settings)
3. **Enable auto-scaling** for high traffic
4. **Backup Chroma data** regularly (from Chroma Cloud dashboard)

## Deployment Architecture

```
┌──────────────────────────────────────┐
│         GitHub Repository            │
│  (server.js, tools.js, Dockerfile)   │
└──────────────┬───────────────────────┘
               │
               │ Push to main
               │
               ▼
┌──────────────────────────────────────┐
│      Render (render.com)             │
│                                      │
│  Docker Build:                       │
│  ├─ Node.js 20 runtime               │
│  ├─ Python 3.11 + Piper TTS          │
│  ├─ Voice model (en_US-lessac)       │
│  └─ npm dependencies                 │
│                                      │
│  Web Service (3000)                  │
│  ├─ API endpoints                    │
│  ├─ Speech-to-text (Deepgram)        │
│  ├─ LLM responses (Gemini)           │
│  ├─ Text-to-speech (Piper)           │
│  └─ Memory (Chroma Cloud)            │
└──────────────┬───────────────────────┘
               │
        ┌──────┼──────┬──────────┐
        │      │      │          │
        ▼      ▼      ▼          ▼
    Deepgram Google  Chroma    Client
    (STT)   Gemini   Cloud    (Browser)
            (LLM)   (Memory)
```

## Cost Breakdown

**Monthly Costs** (approximate, as of 2026):
- Render Web Service: $12 (standard instance)
- Deepgram: $12 (50,000 API calls free, then pay per call)
- Google Gemini: Free tier or pay-as-you-go
- Chroma Cloud: Free tier or $99/month
- **Total**: $24-200/month depending on usage

## Support

- Render docs: https://docs.render.com
- Render support: https://support.render.com
- Voice assistant issues: Check README.md in repo
