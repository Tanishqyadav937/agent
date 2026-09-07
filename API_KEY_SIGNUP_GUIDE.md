# Real API Keys Signup Guide

**Date**: August 28, 2026  
**Status**: Ready to signup (parallel task)

This guide walks you through getting real API keys for weather and web search functionality.

---

## TASK 2: Get Real API Keys

### 1. OpenWeatherMap API Key

**Purpose**: Real-time weather data for any city

**Steps**:
1. Go to: **https://openweathermap.org/api**
2. Click **"Sign Up"** (top right)
3. Fill in the form:
   - Email: Your email
   - Password: Create password
   - Username: Any username
   - Click **Create Account**
4. Verify your email (check inbox for confirmation link)
5. Login to your account
6. Go to **"API keys"** tab (left sidebar or top menu)
7. You'll see a **"Default"** API key
8. **Copy this key** (full 32-character alphanumeric string)

**Example format**: `1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p`

**Free Tier Details**:
- 60 calls per minute
- 1,000,000 calls per month
- All current weather endpoints included
- **Activation time**: Usually 1-2 hours after account creation

**When key is active**, you'll get responses like:
```json
{
  "coord": {"lon": 72.85, "lat": 19.01},
  "main": {"temp": 303.15, "humidity": 65},
  "weather": [{"main": "Sunny", "description": "clear sky"}],
  "wind": {"speed": 8.5}
}
```

---

### 2. Serper.dev API Key

**Purpose**: Google Search API for live web search results

**Steps**:
1. Go to: **https://serper.dev**
2. Click **"Sign Up"** (top right)
3. Choose signup method:
   - Google (easiest, click "Continue with Google")
   - Email (enter email, set password)
4. After signup, you'll land on **Dashboard**
5. Look for **"API Key"** section (usually top or right panel)
6. **Copy this key** (long alphanumeric string)

**Example format**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0`

**Free Tier Details**:
- 100 free searches per month
- Immediate activation (no waiting!)
- Full Google Search results with snippets
- Includes news, shopping, images search

**When key works**, you'll get responses like:
```json
{
  "searchParameters": {...},
  "organic": [
    {
      "position": 1,
      "title": "Result Title",
      "link": "https://example.com",
      "snippet": "Description of the result..."
    }
  ]
}
```

---

## Once You Have Both Keys

**Document them here** (copy-paste after signup):

```
OpenWeatherMap API Key:
_____________________________________

Serper.dev API Key:
_____________________________________

Date Obtained: ________________
```

---

## TASK 3: Configuration & Testing

When you have both keys:

1. **Update .env file**:
   ```bash
   cd /Users/tanishqyadav/agent
   nano .env  # or use your favorite editor
   ```

2. **Replace placeholder keys**:
   ```ini
   # Find these lines and replace with your real keys:
   OPENWEATHER_API_KEY=your_key_here
   SERPER_API_KEY=your_key_here
   ```

3. **Restart backend**:
   ```bash
   pkill -f "npm start"
   sleep 2
   npm start
   ```

4. **Run verification tests** (I'll do this automatically once you provide keys)

---

## Troubleshooting

### OpenWeatherMap Key Not Working
- **Error**: "401 Unauthorized" or "Invalid API key"
- **Solution**: Key still activating (takes 1-2 hours). Wait and retry.
- **Check**: Go to API keys page, verify key is marked "Active"

### Serper Key Not Working  
- **Error**: Empty results or "Unauthorized"
- **Solution**: Copy entire key again (sometimes truncation happens)
- **Check**: Paste into dashboard - should match exactly

### Rate Limit Errors
- **OpenWeather**: You hit 60/minute limit - wait a minute
- **Serper**: You hit 100/month free limit - upgrade plan or wait

---

## Status Tracking

- [ ] OpenWeatherMap signup complete
- [ ] OpenWeatherMap key received and copied
- [ ] OpenWeatherMap key activated (test after 1-2 hours)
- [ ] Serper.dev signup complete
- [ ] Serper.dev key received and copied
- [ ] Updated .env with both keys
- [ ] Backend restarted with new keys
- [ ] Live API test successful (Task 3)

---

## Timeline

- **OpenWeatherMap**: ~2 minutes signup + ~1-2 hours activation = **1.5-2.5 hours total**
- **Serper**: ~2 minutes signup + **immediate activation** = **2 minutes total**
- **Total**: Can start immediately, OpenWeather will be ready in 1-2 hours

You can signup for Serper now and test it immediately, then OpenWeather will be ready soon after.

---

## Files to Update After Keys Arrive

- `.env` - Update OPENWEATHER_API_KEY and SERPER_API_KEY values

## Next Command After Keys

Once keys are ready, run this to test:
```bash
# Backend will auto-test on next request
curl -X POST http://localhost:3000/converse-text \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is the weather in London?", "sessionId": "api_test"}'
```

Should return actual weather data (not mock/fallback text).

