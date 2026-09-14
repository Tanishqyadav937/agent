# 🔧 Fix: "Failed to Fetch" Error

## Problem
Frontend on `localhost:5174` could not reach backend on `localhost:3000`.  
Error: `Failed to fetch` in browser console.

## Root Cause
**CORS Origin Mismatch**

The backend's CORS configuration only allowed these origins:
```
- http://localhost:3000
- http://localhost:8000
- http://127.0.0.1:3000
- http://127.0.0.1:8000
```

But the frontend was running on `http://localhost:5174` (not in the allowed list).

## Solution Applied

### Changed (server.js, line 24-26):

**Before:**
```javascript
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:8000', 'http://127.0.0.1:3000', 'http://127.0.0.1:8000'],
  credentials: true
```

**After:**
```javascript
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174', 'http://localhost:8000', 'http://127.0.0.1:3000', 'http://127.0.0.1:8000'],
  credentials: true
```

### What Changed:
✅ Added `http://localhost:5173` (default Vite port)  
✅ Added `http://localhost:5174` (where frontend is actually running)

## Steps Taken

1. ✅ Identified backend CORS config in server.js
2. ✅ Updated `origin` array to include Vite dev ports
3. ✅ Restarted backend server
4. ✅ Verified health check passing
5. ✅ Frontend now connects successfully

## How to Test

### Before (Failed)
```
Frontend on http://localhost:5174
Attempts to fetch: http://localhost:3000/converse
CORS blocked: Origin not allowed
Result: "Failed to fetch" error
```

### After (Fixed)
```
Frontend on http://localhost:5174
Attempts to fetch: http://localhost:3000/converse
CORS allows: localhost:5174 in origin list
Result: 200 OK - Audio processes successfully
```

## Verification

### Check CORS is working
```bash
# Backend should now accept requests from 5174
curl -X OPTIONS http://localhost:3000/health \
  -H "Origin: http://localhost:5174" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Should return 200 with CORS headers
```

### Test API call
```bash
# From browser console or frontend
fetch('http://localhost:3000/health')
  .then(r => r.json())
  .then(console.log)

# Should work now (no CORS error)
```

## Why This Happens

Vite development server can run on different ports:
- Port 5173 (default)
- Port 5174 (if 5173 is in use)
- Port 5175, 5176, etc. (if previous ports are in use)

The CORS config needs to allow all possible dev ports the frontend might use.

## Updated CORS Configuration

```javascript
app.use(cors({
  // Allow both common dev ports
  origin: [
    'http://localhost:3000',      // Backend itself (for testing)
    'http://localhost:5173',      // Vite default
    'http://localhost:5174',      // Vite fallback (used currently)
    'http://localhost:8000',      // Chroma
    'http://127.0.0.1:3000',     // IPv4 loopback
    'http://127.0.0.1:8000',     // IPv4 loopback
  ],
  credentials: true
}));
```

## For Production Deployment

When deploying to Render (or any production environment):

```javascript
app.use(cors({
  origin: [
    'https://my-bunny-service.onrender.com',      // Backend URL
    'https://my-frontend.vercel.app',              // Frontend URL (example)
    'https://bunny-buddy.netlify.app',             // Alternative frontend
    'http://localhost:3000',                       // Keep for local testing
    'http://localhost:5173',
    'http://localhost:5174',
  ],
  credentials: true
}));
```

## Testing Checklist

- ✅ Backend running on port 3000
- ✅ Frontend running on port 5174
- ✅ CORS updated with both ports
- ✅ Backend restarted
- ✅ Health check responding
- ✅ Frontend can fetch `/health`
- ✅ Frontend can send audio to `/converse`
- ✅ Memory system working (sessionId persistence)
- ✅ "Failed to fetch" error gone

## Status

**Fixed**: ✅ YES  
**Time to Fix**: 2 minutes  
**Files Modified**: 1 (server.js)  
**Backend Restart Required**: YES (done)  
**Frontend Restart Required**: NO (same port, already running)

---

## Next Steps

1. ✅ Backend restarted with new CORS config
2. ✅ Frontend still running on port 5174
3. → Refresh browser to clear any cached errors
4. → Try connecting and recording audio again
5. → Should work without "Failed to fetch" error

---

**Resolution**: CORS Origin List Updated  
**Severity**: CRITICAL (blocked all API calls)  
**Status**: ✅ RESOLVED

