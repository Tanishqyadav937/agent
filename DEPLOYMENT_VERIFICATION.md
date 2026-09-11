# Deployment Verification Guide

Complete guide to verify the voice assistant deployment is working correctly on Render.

## Pre-Deployment Checklist ✅

### Code Quality
- [x] server.js: Syntax validated, no hardcoded secrets
- [x] tools.js: Function implementations complete, error handling in place
- [x] Dockerfile: Multi-stage build, production optimized
- [x] render.yaml: Infrastructure as Code defined and tested
- [x] .gitignore: Secrets excluded, verified with `git check-ignore`
- [x] package.json: All dependencies pinned, no security vulnerabilities
- [x] Environment variables: All documented in ENV_VARIABLES_REFERENCE.md

### Dependencies Verified
```
✅ Node.js (v20)
✅ Express (v4.22.2)
✅ Deepgram SDK (v3.13.0)
✅ Google Generative AI (v0.21.0)
✅ ChromaDB (v1.10.5)
✅ Piper TTS (bundled in Docker)
✅ Python 3.11 (in Docker)
```

### Local Testing Completed
- [x] `npm check` - All API keys configured ✓
- [x] `npm start` - Server starts without errors ✓
- [x] GET /health - Returns JSON status ✓
- [x] POST /converse-text - Full pipeline works (LLM + TTS) ✓
- [x] Error handling - Graceful degradation when services unavailable ✓

---

## Step 1: Connect Repository to Render

### 1.1 Push to GitHub
```bash
cd /Users/tanishqyadav/agent
git add .
git commit -m "Production deployment: Add Docker, render.yaml, and deployment guides"
git push origin main
```

### 1.2 Connect to Render

1. Go to https://dashboard.render.com
2. Click "New" → "Web Service"
3. Choose "GitHub" as source
4. Select your repository
5. Render should auto-detect `render.yaml`

---

## Step 2: Set Environment Variables

In Render dashboard for your service → "Environment":

### Required (Critical)
```
DEEPGRAM_API_KEY=your_key_from_console.deepgram.com
GEMINI_API_KEY=your_key_from_aistudio.google.com
CHROMA_URL=https://api.trychroma.com
CHROMA_API_KEY=your_key_from_chroma_dashboard
```

### Optional (Tools)
```
OPENWEATHER_API_KEY=your_key_from_openweathermap.org
SERPER_API_KEY=your_key_from_serper.dev
```

### Automatic (Already in render.yaml)
```
NODE_ENV=production
LLM_PROVIDER=gemini
PORT=3000
EMBEDDING_MODEL=mxbai-embed-large
TOOLS_ENABLED=true
```

---

## Step 3: Deploy

### Option A: Using render.yaml (Recommended)
- Render auto-detects `render.yaml` in repo root
- Reads all configuration from YAML
- One-click deploy from dashboard

### Option B: Manual Configuration
- Skip YAML, manually set all values in dashboard
- Takes longer but more control

---

## Step 4: Monitor Deployment

### 4.1 Watch Build Progress

In Render dashboard:
1. Go to your service
2. Click "Logs" tab
3. Watch for progress messages:

**Good signs** (watch for these):
```
Building image
Pushing image to registry
Creating container
Installing dependencies
[LLM] Provider: gemini
🎤 Voice Assistant Backend running on port 3000
```

**Bad signs** (indicate problems):
```
Build failed
Cannot find module
API key not configured
ECONNREFUSED (network error)
Ollama not reachable (should not appear in production)
```

### 4.2 Build Time Expectations
- **First build**: 15-20 minutes (Piper compilation from source)
- **Subsequent builds**: 5-10 minutes (layer caching)
- **If > 30 minutes**: Check logs, may be network issue

---

## Step 5: Health Check Verification

### 5.1 Get Your Service URL

In Render dashboard → URL section
Format: `https://voice-assistant-api.onrender.com` (example)

### 5.2 Verify /health Endpoint

```bash
# Test health status
curl https://your-service-url/health | jq .
```

**Expected response (HEALTHY)**:
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

**Interpretation**:
- ✅ status: "healthy" - All critical services working
- ✅ deepgram: true - Speech-to-text ready
- ✅ gemini: true - LLM ready
- ✅ piper: true - Text-to-speech ready
- ✅ chroma: true - Memory persistence ready
- ✅ ollama.note: "not used" - Production correctly skips Ollama

**Degraded response (shows which service failed)**:
```json
{
  "status": "degraded",
  "services": {
    "deepgram": true,
    "gemini": false,      // ❌ Missing GEMINI_API_KEY
    "piper": true,
    "chroma": false,      // ❌ Can't reach Chroma Cloud
    "ollama": {...}
  }
}
```

### 5.3 Fix Health Issues

| Service | Status | Fix |
|---------|--------|-----|
| deepgram | false | Add DEEPGRAM_API_KEY to env vars |
| gemini | false | Add GEMINI_API_KEY to env vars |
| piper | false | Docker build issue (check logs) |
| chroma | false | Add CHROMA_URL + CHROMA_API_KEY |

---

## Step 6: Functional Testing

### 6.1 Test Text Endpoint

```bash
# Simple conversation
curl -X POST https://your-service-url/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session",
    "user_input": "Hello! What is 2 + 2?"
  }' | jq .
```

**Expected response**:
```json
{
  "sessionId": "test_session",
  "user_input": "Hello! What is 2 + 2?",
  "response_text": "2 + 2 equals 4.",
  "audio_base64": "UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQIAAAAAAA=="
}
```

✅ Good signs:
- `response_text` contains coherent answer
- `audio_base64` is non-empty string
- Response time < 5 seconds
- No error messages

❌ Bad signs:
- response_text is empty
- audio_base64 is null or empty
- Status 500 error
- Response contains "Ollama not found"

### 6.2 Test Memory Persistence

```bash
# Store memory
curl -X POST https://your-service-url/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "memory_test",
    "user_input": "My name is Alice and I work as a software engineer"
  }'

# Wait 2 seconds
sleep 2

# Retrieve memory
curl -X POST https://your-service-url/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "memory_test",
    "user_input": "What is my job?"
  }' | jq '.response_text'
```

✅ Good signs:
- Second response mentions "engineer", "software", or similar
- Shows memory was retrieved

❌ Bad signs:
- Response says "I don't know" or ignores context
- Chroma returns false in /health
- Check CHROMA_API_KEY in environment

### 6.3 Test Tool Calling (Optional)

If you have OPENWEATHER_API_KEY set:

```bash
curl -X POST https://your-service-url/converse-text \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "weather_test",
    "user_input": "What is the weather in London?"
  }' | jq '.response_text'
```

✅ Good signs:
- Response contains temperature, condition (e.g., "72°F, Sunny")
- Real weather data, not mock

❌ Bad signs:
- Response contains "mock" or "example"
- Generic response not specific to London
- Check OPENWEATHER_API_KEY

---

## Step 7: Performance Testing

### 7.1 Response Time Baseline

```bash
# Measure response time
time curl -X POST https://your-service-url/converse-text \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "perf_test", "user_input": "Hi"}'
```

**Expected times** (first request may be slower):
- 1st request: 5-10 seconds (includes TTS audio generation)
- Subsequent: 3-5 seconds (cold start after)
- After warmup: 2-3 seconds (typical)

### 7.2 Concurrency Test

```bash
# Test 3 concurrent requests
for i in {1..3}; do
  curl -X POST https://your-service-url/converse-text \
    -H "Content-Type: application/json" \
    -d "{\"sessionId\": \"concurrent_$i\", \"user_input\": \"Test $i\"}" &
done
wait
```

✅ Good signs:
- All 3 requests complete successfully
- No 503 / overload errors

❌ Bad signs:
- Timeout after 30 seconds
- 503 Service Unavailable
- May need larger instance (Pro plan)

---

## Step 8: Monitor Logs

### 8.1 Regular Monitoring

In Render dashboard → Logs tab:

**Watch for**:
```
[LLM] Provider: gemini        # ✅ Using Gemini (not Ollama)
[Chroma] URL: https://...     # ✅ Using Chroma Cloud
[Memory] Retrieved: X memories # ✅ Memory working
```

**Alert on**:
```
error                          # ❌ Application errors
Cannot reach                   # ❌ Service unreachable
API error                      # ❌ API key invalid
```

### 8.2 Enable Persistent Logs

Render stores logs for 7 days by default. For longer retention:
- Upgrade to Pro plan
- Or use third-party logging (Loggly, Datadog)

---

## Step 9: Production Monitoring Setup

### 9.1 Error Alerts

1. Go to service settings
2. → Notifications
3. Add email for deployment failures

### 9.2 Uptime Monitoring

Use free monitoring service:
- https://uptimerobot.com
- https://www.pingdom.com
- Add your `/health` endpoint as monitor

### 9.3 API Usage Monitoring

Track costs on provider dashboards:
- Deepgram: https://console.deepgram.com → Usage
- Google: https://console.cloud.google.com → Usage

---

## Common Issues & Fixes

### Issue: "Ollama not reachable" in /health
**Cause**: LLM_PROVIDER still set to 'local'
**Fix**: 
```bash
# In Render environment variables:
LLM_PROVIDER=gemini
# Redeploy
```

### Issue: "Chroma API error: 401 Unauthorized"
**Cause**: Invalid or missing CHROMA_API_KEY
**Fix**:
1. Go to Chroma Cloud dashboard
2. Regenerate API key
3. Update in Render environment variables
4. Restart service

### Issue: /health shows "deepgram": false
**Cause**: DEEPGRAM_API_KEY not set
**Fix**:
1. Get key from https://console.deepgram.com
2. Add to Render environment variables
3. Redeploy

### Issue: response_text empty or TTS audio missing
**Cause**: Piper TTS failed in Docker build
**Fix**:
1. Check Render build logs for errors
2. Manually rebuild: In Render dashboard → Redeploy
3. Wait 15+ minutes for full build

### Issue: Memory not persisting across sessions
**Cause**: Chroma not initialized or wrong URL
**Fix**:
1. Verify `/health` shows `"chroma": true`
2. Check CHROMA_URL format (https://, not http://)
3. Verify CHROMA_API_KEY is set

### Issue: Build takes > 30 minutes
**Cause**: Piper building from source is slow
**Fix**:
- First build always slow (compiles Piper)
- Subsequent builds use Docker layers (faster)
- If stuck > 30 min, check Render logs for errors

---

## Deployment Success Checklist

- [ ] Repository pushed to GitHub
- [ ] Render service created and connected
- [ ] All environment variables set
- [ ] `/health` endpoint returns status: "healthy"
- [ ] /converse-text responds with real LLM output
- [ ] Audio base64 is non-empty
- [ ] Memory persistence test passed
- [ ] Response time is acceptable (< 5 sec)
- [ ] Logs show no errors
- [ ] Monitoring alerts configured
- [ ] Team notified of service URL

---

## Production Runbook

### Daily Checks
1. Verify /health status is "healthy"
2. Scan logs for errors
3. Check API usage (Deepgram, Google)

### Weekly Checks
1. Test /converse-text endpoint
2. Verify memory persistence works
3. Check Render uptime metrics

### Monthly Checks
1. Review API costs
2. Rotate API keys (recommended)
3. Update dependencies
4. Full regression test

### On Deployment Issues
1. Check `/health` endpoint
2. Review Render logs (Logs tab)
3. Verify environment variables are set
4. Redeploy service
5. If still failing, check SECURITY_CHECKLIST.md

---

## Rollback Procedure

If deployment has critical issues:

1. **Immediate**: Revert to previous commit
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **In Render**: Click "Redeploy" to rebuild from previous commit

3. **Verify**: Check `/health` endpoint

4. **Post-incident**: Review what went wrong, fix locally, test before redeploying

---

## Next Steps After Successful Deployment

1. **Set up custom domain** (optional)
2. **Enable auto-scaling** for high traffic
3. **Configure monitoring** for key metrics
4. **Document your service URL** for team
5. **Test integration** with frontend/avatar UI
6. **Plan maintenance window** for updates

---

## Support

- **Render documentation**: https://docs.render.com
- **Server.js issues**: Check logs in Render dashboard
- **API key issues**: Check respective provider dashboards
- **Chroma issues**: See CHROMA_CLOUD_SETUP.md
- **General troubleshooting**: See RENDER_DEPLOYMENT_GUIDE.md
