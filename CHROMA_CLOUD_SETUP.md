# Chroma Cloud Setup Guide for Production

## Overview
This guide explains how to set up Chroma Cloud for the voice assistant's memory persistence on Render.

## Why Chroma Cloud?
- **Persistent**: Memory survives app restarts
- **Hosted**: No need to run a separate Chroma server on Render
- **Scalable**: Handles multiple sessions automatically
- **Free Tier**: Good for testing (requests-based limits)

## Setup Steps

### 1. Create a Chroma Cloud Account
1. Go to https://www.trychroma.com/
2. Click "Get Started" or "Sign Up"
3. Create an account with email/password
4. Verify your email

### 2. Create a New Project
1. After login, go to the dashboard
2. Click "New Project" or similar button
3. Give it a name (e.g., "voice-assistant-prod")
4. Select region closest to your Render location (usually US East)
5. Click "Create"

### 3. Get Your Credentials
1. In the project dashboard, find "API Settings" or "Connection"
2. Copy the following:
   - **Chroma Cloud URL** (format: `https://api.trychroma.com` or similar)
   - **API Key** (also called "Authentication Token")

### 4. Set Environment Variables on Render

In your Render service dashboard, add these environment variables:

```
CHROMA_URL=https://api.trychroma.com
CHROMA_API_KEY=your_api_key_from_step_3
```

### 5. Update Local .env (Development)

For local development, you can either:
- **Use local Chroma**: Keep defaults
  ```
  CHROMA_URL=http://localhost:8000
  # No CHROMA_API_KEY needed
  ```
- **Test against cloud**: Use cloud credentials
  ```
  CHROMA_URL=https://api.trychroma.com
  CHROMA_API_KEY=your_api_key
  ```

Start local Chroma server:
```bash
# If using local Chroma
docker run -p 8000:8000 chromadb/chroma
```

## Verification

### Local Test
```bash
# Start backend
npm start

# Test memory persistence
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "chroma_test",
    "user_input": "My name is Alex and I work as a developer"
  }'

# Should respond with memory stored

# Test memory retrieval (restart and test)
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "chroma_test",
    "user_input": "What is my name?"
  }'

# Should recall: "Your name is Alex"
```

### Production Verification (on Render)

After deploying to Render:

```bash
# Check health endpoint
curl https://your-render-service-url/health

# Should show:
# {
#   "status": "healthy",
#   "services": {
#     "chroma": true,
#     ...
#   }
# }
```

## Troubleshooting

### "Chroma API error: 401 Unauthorized"
- **Cause**: Invalid or missing API key
- **Fix**: 
  - Verify `CHROMA_API_KEY` is correct in Render dashboard
  - Regenerate key in Chroma Cloud dashboard if needed
  - Ensure key is set as environment variable, not hardcoded

### "Cannot reach Chroma: ECONNREFUSED"
- **Cause**: Using localhost URL in production (Render can't reach your local machine)
- **Fix**:
  - Set `CHROMA_URL=https://api.trychroma.com` in Render environment
  - Use actual Chroma Cloud URL, not localhost

### "Chroma server not reachable"
- **Cause**: Network connectivity issue
- **Fix**:
  - Check internet connectivity on Render
  - Verify CHROMA_URL format is correct
  - Check Chroma Cloud status at their website

### Memory not persisting across restarts
- **Cause**: Chroma client not initialized properly
- **Fix**:
  - Check `/health` endpoint to verify `chroma: true`
  - Verify `CHROMA_API_KEY` environment variable is set
  - Check Render logs for initialization errors

## Architecture

```
┌─────────────────┐
│  Voice Assistant│
│  Backend (Node) │
│                 │
│  server.js      │
│  (Production)   │
└────────┬────────┘
         │
         │ CHROMA_URL + CHROMA_API_KEY
         │
         ▼
┌─────────────────┐
│  Chroma Cloud   │
│  (Hosted)       │
│  api.trychroma  │
│  .com           │
└─────────────────┘
         │
         │ (Internet)
         │
    ┌────▼────┐
    │Database │
    │Storage  │
    └─────────┘
```

## Cost Considerations

**Chroma Free Tier**:
- Limited requests per month
- Good for development/testing
- Upgrade to Pro if you exceed limits

**Estimation**:
- Each conversation turn = ~5-10 API calls (embedding + retrieval)
- 100 daily users × 10 turns × 8 calls = 8,000 calls/day
- Check Chroma pricing page for current limits

## Next Steps

1. Finish setting up environment variables in Render (see Tasks #5-#6)
2. Deploy the backend to Render
3. Test `/health` endpoint to verify Chroma connectivity
4. Run end-to-end test with memory persistence
