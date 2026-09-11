# Security Checklist for Production Deployment

## Secrets Management ✅

### .gitignore Configuration
- [x] `.env` excluded from git
- [x] `.env.local` excluded from git
- [x] `.env.production.local` excluded from git
- [x] `.env.bak` excluded from git
- [x] Backup files (`*.bak`, `*.key`, `*.pem`) excluded
- [x] `.env.example` is committed (template only, no secrets)

**Verification**:
```bash
git check-ignore -v .env           # Should show .gitignore:2
git check-ignore -v .env.bak       # Should show .gitignore:XX
git ls-files | grep "^\.env"       # Should show only .env.example
```

### API Keys and Secrets
- [x] No API keys hardcoded in JavaScript files
- [x] All secrets read from environment variables only
- [x] `.env` files only exist locally and never in version control
- [x] Render environment variables used for production secrets

**Where to Set Secrets**:
- **Development**: In local `.env` file (never committed)
- **Production**: In Render dashboard → Environment Variables (encrypted at rest)
- **Never**: Hardcoded in code, committed to git, or exposed in logs

---

## API Key Rotation ⚠️ (Important)

### Current State
The repository contains old API keys in git history (in `.env.bak`):
- `DEEPGRAM_API_KEY=c94c49c55aff1bc3ea9b3f260c38f1849de18cec`
- `GEMINI_API_KEY=AQ.Ab8RN6JxB7evRMno9RqJ1PBbbr7GnZ7jF9yMxP-BBHEDSEIUtA`
- `ELEVENLABS_API_KEY=sk_26dc99e21715554cce65f12272b992fe179b39398d0c85ac`

### Recommended Actions
1. **Immediately** (if using these keys in production):
   - [ ] Rotate/regenerate all API keys on their respective platforms
   - [ ] Update local `.env` with new keys
   - [ ] Update Render environment variables with new keys
   - [ ] Test that services still work

2. **Git History Cleanup** (optional but recommended):
   ```bash
   # Warning: This rewrites git history. Do only if keys were compromised.
   # Better approach: Assume keys are rotated and monitor for misuse
   git filter-repo --invert-paths --path .env.bak
   git push origin --force-with-lease
   ```

3. **Monitor for Misuse**:
   - Check API usage logs on Deepgram, Google, ElevenLabs dashboards
   - Look for unusual activity or unauthorized API calls
   - Set up billing alerts to catch suspicious usage

---

## Environment Variable Security

### Render Dashboard
- [x] All secrets set as environment variables (not in code)
- [x] Secrets encrypted at rest by Render
- [x] No secrets logged in console output
- [x] `/health` endpoint doesn't expose secrets

### Development Machine
- [x] `.env` file on local machine only
- [x] `.env` in `.gitignore` (not committed)
- [x] File permissions: `chmod 600 .env` (read-only for user)

```bash
# Verify permissions on local machine
ls -la .env
# Should show: -rw------- (600) owner
```

---

## Code Security

### No Secrets in Code
- [x] No API keys in JavaScript
- [x] No hardcoded secrets in Docker image
- [x] No secrets in logs (console.log, error messages)
- [x] No secrets in comments

**Search verification**:
```bash
# Check for accidental key patterns
grep -r "DEEPGRAM_API_KEY=" *.js *.ts 2>/dev/null || echo "✓ No hardcoded keys"
grep -r "sk_" *.js *.ts 2>/dev/null | grep -v process.env || echo "✓ No secrets in code"
```

### Dockerfile Security
- [x] Piper binary downloaded from official source (not from untrusted repo)
- [x] Python packages from official PyPI
- [x] Node packages from official npm registry
- [x] No secrets in Dockerfile (all from env vars at runtime)

---

## API Security

### Deepgram (Speech-to-Text)
- [x] API key has minimal required scope
- [x] Used only for `/converse` and `/converse-text` endpoints
- [x] Error messages don't expose key or raw API errors

### Google Gemini (LLM)
- [x] API key scoped to Generative AI API only
- [x] Rate limiting: Free tier limits protect against misuse
- [x] Monitor usage at https://aistudio.google.com/app/apikeys

### Chroma Cloud (Memory)
- [x] API key separate from database password
- [x] Network requests to Chroma use HTTPS only
- [x] API key in environment variable (not hardcoded)

### Tool APIs (Weather, Search)
- [x] OpenWeather and Serper keys scoped to their services
- [x] Rate limiting set on provider side
- [x] Fallback to mock responses if keys missing

---

## Network Security

### HTTPS Only (Production)
- [x] Render automatically provides HTTPS
- [x] All external API calls use HTTPS
- [x] `.env` never transmitted over network (local only)

### CORS Configuration
- [x] CORS enabled for frontend origins only
- [x] Development: `localhost:3000`, `localhost:8000`, `127.0.0.1`
- [x] Production: Should be set in environment if needed

```javascript
// From server.js
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:8000', 'http://127.0.0.1:3000', 'http://127.0.0.1:8000'],
  credentials: true
}));
```

### Port Exposure
- [x] Port 3000 accessible only through Render's proxy
- [x] No direct port exposure on Render (firewalled)
- [x] Public URL through Render's domain

---

## Logging & Monitoring

### Sensitive Data in Logs
- [x] No API keys in console.log output
- [x] Error messages sanitized (don't expose internals)
- [x] User input echoed but not API responses containing sensitive data

**Log review**:
```bash
# Check server logs for sensitive patterns
npm start 2>&1 | grep -i "key\|secret\|auth" || echo "✓ No secrets in logs"
```

### Monitoring
- [ ] Set up Render alerts for high error rates
- [ ] Monitor API usage on provider dashboards
- [ ] Check Render logs regularly for errors

---

## Deployment Security

### Before Deployment
- [x] All secrets set in Render environment (not in code)
- [x] `.env` file not committed (verified with `git ls-files`)
- [x] `.gitignore` properly configured
- [x] Dockerfile doesn't include secrets

### After Deployment
- [ ] Test `/health` endpoint (should show all services healthy)
- [ ] Verify API calls work with real credentials
- [ ] Check that mock responses don't appear (means real APIs working)
- [ ] Monitor Render logs for errors

---

## Docker Security

### Image Scanning
```bash
# Build locally to test
docker build -t voice-assistant-prod .

# Check image for known vulnerabilities (if Docker Scout available)
docker scout cves voice-assistant-prod
```

### Base Image
- [x] Using official `node:20-slim` (minimal, regularly updated)
- [x] Using official `python:3.11-slim` (minimal, regularly updated)
- [x] Not using `latest` tags (specific versions pinned)

### Build Best Practices
- [x] Multi-stage build (reduces final image size)
- [x] `.dockerignore` excludes unnecessary files
- [x] No secrets in Docker build

---

## Incident Response

### If API Key Compromised
1. **Immediately**:
   - Rotate the compromised key in provider dashboard
   - Update local `.env` with new key
   - Update Render environment variable
   - Restart service on Render

2. **Within 24 hours**:
   - Check API logs for unauthorized usage
   - Calculate potential cost of misuse
   - File abuse report with provider if needed

3. **Document**:
   - Date/time of compromise discovery
   - Actions taken
   - Any unauthorized usage found
   - New key generated date

### If Repository Compromised
1. **Rotate all API keys** (see above)
2. **Review recent commits** for any added secrets
3. **Force push** if history needs cleaning (coordinate with team)
4. **Monitor** for any signs of exploitation

---

## Checklist for Production Launch

- [ ] All API keys rotated and secured
- [ ] `.env` and `*.bak` files excluded from git
- [ ] No secrets found in code/comments
- [ ] Render environment variables set (not in code)
- [ ] Dockerfile doesn't contain secrets
- [ ] HTTPS enabled (Render default)
- [ ] CORS properly configured for frontend
- [ ] `/health` endpoint working
- [ ] API calls return real data (not mock)
- [ ] Logs don't expose secrets
- [ ] Backup plan for API key rotation ready

---

## Resources

- **Git security**: https://docs.github.com/en/code-security/secret-scanning
- **Render security**: https://render.com/docs/security
- **OWASP secrets management**: https://owasp.org/www-project-secrets-management/
- **API key rotation best practices**: https://cloud.google.com/docs/authentication/manage-keys

---

## Questions?

Review `ENV_VARIABLES_REFERENCE.md` for how to properly set each secret.
