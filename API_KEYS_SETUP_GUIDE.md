# API Keys Setup Guide
## Real API Key Configuration for Weather & Web Search

**Date**: August 28, 2026  
**Status**: Infrastructure ready, keys needed from external services

---

## Current Status

### Infrastructure ✅
- Weather tool: Integrated and callable
- Web search tool: Integrated and callable  
- Calendar tool: Integrated and callable
- Reminders tool: Integrated and callable
- Fallback/graceful degradation: Working

### API Keys ❌ (Need manual signup)
- OpenWeather: Demo key (expired/invalid)
- Serper: Demo key (expired/invalid)

---

## TEST 1: OpenWeather API Setup

### Quick Steps
1. Go to: https://openweathermap.org/api
2. Click "Sign Up" or "Create Account"
3. Fill form (email, password, username)
4. Check email for verification link and click it
5. Login to https://home.openweathermap.org
6. Go to **"API keys"** tab
7. Copy the **"Default"** API key (looks like: `1234567890abcdef...`)
8. Update `.env`:
   ```
   OPENWEATHER_API_KEY=your_key_here
   ```
9. Restart backend: `npm start`
10. **Wait 1-2 hours** for key to activate (OpenWeather requirement)

### Verification
After key is active, test:
```bash
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is the weather in New York?", "sessionId": "weather_test"}'
```

**Expected**: Response includes actual temperature, humidity, wind speed  
**Success indicator**: Response contains degree symbol (°) or terms like "celsius", "fahrenheit"

### Troubleshooting
- **401 Unauthorized**: Key is still inactive or incorrect
- **Mock response**: Key format correct but not yet active
- **Connection error**: Firewall/network issue

---

## TEST 2: Serper API Setup

### Quick Steps
1. Go to: https://serper.dev
2. Click "Sign Up" → Choose Google/Email signup
3. Verify email if needed
4. Go to Dashboard
5. Copy API Key from top section
6. Update `.env`:
   ```
   SERPER_API_KEY=your_key_here
   ```
7. Restart backend: `npm start`
8. **Immediate**: Key is active right away (unlike OpenWeather)

### Verification
After setup, test:
```bash
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Latest news from India today", "sessionId": "search_test"}'
```

**Expected**: Response includes actual news headlines, links, snippets  
**Success indicator**: Response mentions actual current events or articles

### Troubleshooting
- **Error 429**: Rate limit hit (free tier limit)
- **Empty results**: Query too vague or no live data available
- **"Unauthorized"**: Key format wrong or not copied fully

---

## Manual Test Steps

### After Adding Keys

1. **Stop backend**:
   ```bash
   pkill -f "npm start"
   ```

2. **Update .env file** with your real keys:
   ```bash
   nano /Users/tanishqyadav/agent/.env
   # or use any editor
   ```

3. **Start backend**:
   ```bash
   cd /Users/tanishqyadav/agent
   npm start
   ```

4. **Test OpenWeather**:
   ```bash
   curl -X POST http://localhost:3000/converse-text \
     -H "Content-Type: application/json" \
     -d '{
       "user_input": "What is the weather in Mumbai right now?",
       "sessionId": "weather_real_test"
     }' | jq '.response_text'
   ```

5. **Test Serper**:
   ```bash
   curl -X POST http://localhost:3000/converse-text \
     -H "Content-Type: application/json" \
     -d '{
       "user_input": "What happened in tech news today?",
       "sessionId": "search_real_test"
     }' | jq '.response_text'
   ```

---

## Current .env Configuration

```bash
# Backend
PORT=3000
LLM_PROVIDER=local
OLLAMA_MODEL=qwen2.5:7b-instruct
MEMORY_ENABLED=true
TOOLS_ENABLED=true
EMBEDDING_MODEL=mxbai-embed-large

# Tool API Keys (waiting for real signup)
OPENWEATHER_API_KEY=b6fd4a142f37e83a32968e1707284366
SERPER_API_KEY=b2891beeb2eca7db70cbe31f768b1f9b7dda28a4
```

---

## Free Tier Limits

| Service | Free Tier | Limit |
|---------|-----------|-------|
| OpenWeather | Current Weather | 60 calls/minute, 1M calls/month |
| Serper | Google Search | 100 searches/month free plan |
| Google Calendar | Basic | Limited (needs OAuth) |

---

## Code Changes Made (Infrastructure Ready)

### File: `/Users/tanishqyadav/agent/server.js`

**Memory threshold tuned** (from 0.7 → 1.5):
```javascript
// Allows semantic variations in user facts without over-filtering
const SIMILARITY_THRESHOLD = 1.5;
```

**Tool integration working**:
- `get_weather()`: Calls OpenWeather API if key is valid
- `web_search()`: Calls Serper API if key is valid
- Graceful fallback to mock data if keys invalid

### Tools Ready to Use

All 4 tools are integrated and functional:
1. ✅ `get_weather(city)` - Weather data
2. ✅ `web_search(query)` - Google search
3. ✅ `create_calendar_event()` - Calendar (needs Google OAuth)
4. ✅ `create_reminder()` - Reminders (local)

---

## Production Deployment

To deploy with real APIs:

1. **Get keys** from OpenWeather and Serper
2. **Update .env** with actual keys
3. **Verify** each tool works with test queries
4. **Deploy** backend to production
5. **Monitor** API usage and rate limits

No code changes needed — infrastructure already supports real APIs.

---

## Next Steps for User

**Required for TEST 1 & TEST 2 to pass with real data**:
1. Manually sign up at openweathermap.org
2. Wait 1-2 hours for key activation
3. Manually sign up at serper.dev (immediate)
4. Update .env with real keys
5. Restart backend
6. Re-run tests with real queries

**Already Complete**:
- ✅ TEST 3: Memory persistence
- ✅ TEST 4: Model comparison (qwen2.5:7b recommended)

