# Chroma Cloud Migration Guide

## 🎯 Changes Made

### 1. **Code Updates in server.js**

**Import Change:**
```javascript
// Before
import { ChromaClient } from 'chromadb';

// After
import { CloudClient } from 'chromadb';
```

**Client Initialization:**
```javascript
// Before (local or cloud with URL + auth)
const CHROMA_URL = process.env.CHROMA_URL || 'http://localhost:8000';
const CHROMA_API_KEY = process.env.CHROMA_API_KEY || null;

let chromaClient;
if (CHROMA_API_KEY) {
  chromaClient = new ChromaClient({
    path: CHROMA_URL,
    auth: { provider: 'token', credentials: CHROMA_API_KEY }
  });
} else {
  chromaClient = new ChromaClient({ path: CHROMA_URL });
}

// After (Chroma Cloud only)
const CHROMA_API_KEY = process.env.CHROMA_API_KEY;
const CHROMA_TENANT = process.env.CHROMA_TENANT;
const CHROMA_DATABASE = process.env.CHROMA_DATABASE;

let chromaClient;
if (CHROMA_API_KEY && CHROMA_TENANT && CHROMA_DATABASE) {
  chromaClient = new CloudClient({
    apiKey: CHROMA_API_KEY,
    tenant: CHROMA_TENANT,
    database: CHROMA_DATABASE
  });
} else {
  console.warn('[Chroma] Missing required Cloud credentials');
  chromaClient = null;
}
```

### 2. **Environment Variables Updated**

**Removed:**
- `CHROMA_URL` (no longer needed)

**Added:**
- `CHROMA_API_KEY` - Your Chroma Cloud API key
- `CHROMA_TENANT` - Your tenant ID (UUID format)
- `CHROMA_DATABASE` - Your database name

**Note:** `CHROMA_HOST` is NOT needed — CloudClient defaults to `api.trychroma.com`

### 3. **.env.example Updated**

Old format (removed):
```
CHROMA_URL=http://localhost:8000
# CHROMA_URL=https://api.trychroma.com
# CHROMA_API_KEY=your_chroma_api_key_here
```

New format (added):
```
# ========================
# Embedding & Memory (Chroma Cloud)
# ========================
# Chroma Cloud (https://www.trychroma.com/)
# Get credentials from Chroma dashboard's "Configure SDK" page
CHROMA_API_KEY=your_chroma_api_key_here
CHROMA_TENANT=your_chroma_tenant_id_here
CHROMA_DATABASE=your_chroma_database_name_here

# Note: CHROMA_HOST defaults to api.trychroma.com automatically
# No need to set it unless using a non-default region
```

## 📋 Files Changed

| File | Change | Reason |
|------|--------|--------|
| `server.js` | Updated import & client init | Switch to CloudClient API |
| `.env.example` | Updated var names & docs | Document new required vars |
| `.env` | Updated var names | Match new requirements |

## 🔧 What You Need To Do

### Step 1: Get Your Chroma Cloud Credentials

1. Go to [https://console.trychroma.com/](https://console.trychroma.com/)
2. Log in or create a free account
3. Create a new organization/database if needed
4. Click "Configure SDK" in the dashboard
5. Copy your credentials:
   - **API Key** → `CHROMA_API_KEY`
   - **Tenant** → `CHROMA_TENANT`
   - **Database** → `CHROMA_DATABASE`

### Step 2: Update `.env` on Your Local Machine

Replace the placeholder values in `.env`:

```bash
# Paste your real values from Chroma Cloud dashboard
CHROMA_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CHROMA_TENANT=7d4e76ec-8270-407c-b9ef-c0fa76e3f424
CHROMA_DATABASE=agent-db
```

⚠️ **Important:** Never commit real credentials to the repo. Keep `.env` in `.gitignore` and only update `.env.example` with placeholder values.

### Step 3: Test the Connection Locally

```bash
node test-chroma-cloud.js
```

Expected output:
```
🧪 Testing Chroma Cloud Connection...

Configuration:
  API Key: ✓ Set
  Tenant: ✓ 7d4e76ec-8270-407c-b9ef-c0fa76e3f424
  Database: ✓ agent-db

Connecting to Chroma Cloud...
✓ CloudClient instantiated

Getting or creating collection "test_connection"...
✓ Collection retrieved/created

Adding test document...
✓ Document added successfully

Retrieving test document...
✓ Document retrieved

Cleaning up test document...
✓ Test document deleted

✅ All Chroma Cloud tests passed!
```

If you see errors, check:
1. API key is correct (copy-paste from dashboard, no extra spaces)
2. Tenant ID is correct
3. Database name is correct
4. Network connectivity to `api.trychroma.com`

### Step 4: Update Render Deployment

In your Render dashboard for your backend service:

1. Go to **Environment → Environment Variables**
2. **Remove:** `CHROMA_URL` (if it exists)
3. **Add/Update:**
   - `CHROMA_API_KEY` = [your key from dashboard]
   - `CHROMA_TENANT` = [your tenant ID]
   - `CHROMA_DATABASE` = [your database name]

4. **Do NOT add:** `CHROMA_HOST` (CloudClient defaults to api.trychroma.com)

5. Click **Save** and trigger a redeploy

### Step 5: Redeploy & Test

After updating Render env vars:

1. In Render dashboard, click **Redeploy** on your backend service
2. Watch the deploy logs for errors
3. Once deployed, check health endpoint:
   ```bash
   curl https://your-backend.onrender.com/health | jq '.services.chroma'
   ```
4. Should see: `"chroma": true`

## 🚀 How It Works

### Before (Broken in Production)
```
Local Machine: ✓ Chroma on localhost:8000
Render Cloud: ✗ No Chroma server (connection fails)
```

### After (Chroma Cloud)
```
Local Machine: ✓ CloudClient → api.trychroma.com
Render Cloud:  ✓ CloudClient → api.trychroma.com
(Same connection path, no local dependency)
```

## 🔐 Security Notes

1. **API Key Protection:**
   - `.env` is in `.gitignore` ✓ (not committed)
   - `.env.example` has placeholder values ✓ (safe to commit)
   - Render env vars are encrypted ✓

2. **Network Security:**
   - CloudClient uses HTTPS to api.trychroma.com
   - API key is sent securely in headers
   - No data stored locally in production

## 📊 Chroma SDK Info

- **Version:** chromadb@1.10.5
- **Client Type:** CloudClient (managed vector database)
- **Host:** api.trychroma.com (automatic, no config needed)
- **Auth:** API key based
- **Features:** Full Chroma API compatibility

## ✅ Verification Checklist

Before deploying to Render:

- [ ] Local `.env` has real Chroma Cloud credentials
- [ ] `test-chroma-cloud.js` passes successfully
- [ ] `server.js` imports `CloudClient` (not `ChromaClient`)
- [ ] No `CHROMA_URL` references in code (grep to verify)
- [ ] `.env.example` only has placeholder values
- [ ] `.gitignore` includes `.env` (don't commit secrets)

Before redeploying Render:

- [ ] Render env vars set: CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE
- [ ] Render env vars removed: CHROMA_URL (if present)
- [ ] Backend redeploy completed
- [ ] `/health` endpoint shows `chroma: true`

## 🆘 Troubleshooting

### CloudClient Not Found Error
```
Error: Cannot find module 'chromadb' or CloudClient not exported
```
**Solution:** Verify chromadb is installed: `npm ls chromadb`
Should show: `chromadb@1.10.5` or higher

### API Key Invalid
```
Error: Invalid API key for Chroma Cloud
```
**Solution:** 
1. Double-check key from dashboard (no spaces)
2. Verify it's the SDK API key, not an account key
3. Generate a new key if unsure

### Tenant/Database Not Found
```
Error: Tenant or database does not exist
```
**Solution:** 
1. Verify tenant ID and database name match dashboard
2. Create a new database in Chroma Cloud if needed
3. Check for typos (tenant ID is a UUID)

### Connection Timeout
```
Error: Connection to api.trychroma.com timed out
```
**Solution:**
1. Check network connectivity: `curl https://api.trychroma.com`
2. Check firewall/VPN not blocking outbound HTTPS
3. Render may need outbound network access enabled

## 📚 Resources

- [Chroma Cloud Docs](https://docs.trychroma.com/cloud/)
- [Chroma JS SDK](https://docs.trychroma.com/reference/py-client)
- [Chroma Dashboard](https://console.trychroma.com/)
- [Getting Started](https://docs.trychroma.com/cloud/getting-started)

## 🎉 Summary

- ✅ Code migrated to CloudClient
- ✅ Environment variables updated
- ✅ No local Chroma dependency in production
- ✅ Same API compatibility (no breaking changes)
- ✅ Ready for Render deployment

Next step: Add credentials to .env, run test script, then update Render!

