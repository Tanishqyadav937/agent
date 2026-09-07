# Testing Guide - Phase 2: Conversation Memory

This guide covers testing the conversation memory features added in Phase 2.

## Prerequisites

1. Server is running: `npm start`
2. Test audio file exists: `test2.wav`
3. API keys are configured in `.env`

## Test Categories

### 1. Basic Memory Flow

#### Test 1.1: New Session with Empty Memory

**Goal**: Verify the system works correctly with no previous conversation or memories.

**Steps**:
```bash
SESSION_ID="test-new-session"

curl -X POST http://localhost:3000/converse \
  -F "audio=@test2.wav" \
  -F "sessionId=$SESSION_ID" \
  -o test-1-1.wav
```

**Expected**:
- HTTP 200
- Server logs: `[Memory] Session: test-new-session - New session created`
- Server logs: `[Memory] Retrieved: 0 memories`
- Audio response generated successfully

---

#### Test 1.2: Second Request in Same Session

**Goal**: Verify conversation history is retained within a session.

**Steps**:
```bash
curl -X POST http://localhost:3000/converse \
  -F "audio=@test2.wav" \
  -F "sessionId=$SESSION_ID" \
  -o test-1-2.wav
```

**Expected**:
- HTTP 200
- Session now has 2 turns in memory
- Context includes previous turn
- Audio response generated

---

### 2. Rolling 10-Turn Buffer

#### Test 2.1: Exceed 10 Turns

**Goal**: Verify only the last 10 turns are kept in memory.

**Steps**:
```bash
SESSION_ID="test-rolling-buffer"

# Send 12 requests
for i in {1..12}; do
  echo "Request $i"
  curl -X POST http://localhost:3000/converse \
    -F "audio=@test2.wav" \
    -F "sessionId=$SESSION_ID" \
    -o rolling-$i.wav \
    -s
done
```

**Expected**:
- All 12 requests succeed
- After request 11, server logs: `[Memory] Removed oldest turn, kept last 10`
- Session buffer contains only turns 3-12 (last 10)

---

### 3. Session Isolation

#### Test 3.1: Different Sessions Don't Share Memory

**Goal**: Verify sessions are completely isolated.

**Steps**:
```bash
# Session A
curl -X POST http://localhost:3000/converse \
  -F "audio=@test2.wav" \
  -F "sessionId=session-a" \
  -o session-a-1.wav

# Session B (should have no knowledge of Session A)
curl -X POST http://localhost:3000/converse \
  -F "audio=@test2.wav" \
  -F "sessionId=session-b" \
  -o session-b-1.wav
```

**Expected**:
- Server logs show two separate sessions created
- Session B logs: `[Memory] Session: session-b - New session created`
- Session B has no access to Session A's conversation history

---

### 4. Durable Memory Extraction

#### Test 4.1: Store a User Preference

**Goal**: Verify the system extracts and stores durable memories.

**Requirement**: Record or use an audio file saying "I prefer dark mode" or similar preference.

**Steps**:
```bash
SESSION_ID="test-memory-extraction"

# Audio should say: "I prefer dark mode"
curl -X POST http://localhost:3000/converse \
  -F "audio=@preference-audio.wav" \
  -F "sessionId=$SESSION_ID" \
  -o memory-extract.wav
```

**Expected**:
- HTTP 200
- Server logs: `[Memory] Extracting durable memory...`
- Server logs: `[Memory] Extracted durable fact: "User prefers dark mode"`
- Server logs: `[Memory] Stored memory: mem_<uuid> for session <sessionId>`
- Audio response acknowledges the preference

---

#### Test 4.2: Non-Memorable Content

**Goal**: Verify questions/greetings are NOT stored as memories.

**Requirement**: Audio saying "What's the weather?" or "Hello"

**Steps**:
```bash
SESSION_ID="test-no-memory"

# Audio should say: "What's the weather?"
curl -X POST http://localhost:3000/converse \
  -F "audio=@question-audio.wav" \
  -F "sessionId=$SESSION_ID" \
  -o no-memory.wav
```

**Expected**:
- HTTP 200
- Server logs: `[Memory] Extracting durable memory...`
- NO log showing "Extracted durable fact"
- NO log showing "Stored memory"
- Audio response answers the question normally

---

### 5. Memory Retrieval

#### Test 5.1: Retrieve Stored Memory

**Goal**: Verify stored memories are retrieved and used in responses.

**Prerequisite**: Complete Test 4.1 (store a preference)

**Requirement**: Audio asking "What do I prefer?" or referencing the stored preference

**Steps**:
```bash
# Same session as Test 4.1
SESSION_ID="test-memory-extraction"

# Audio should say: "What are my preferences?"
curl -X POST http://localhost:3000/converse \
  -F "audio=@recall-audio.wav" \
  -F "sessionId=$SESSION_ID" \
  -o memory-recall.wav
```

**Expected**:
- HTTP 200
- Server logs: `[Memory] Retrieved: 1 memories` (or more)
- Audio response mentions "dark mode" or the stored preference
- Context passed to Gemini includes the retrieved memory

---

#### Test 5.2: Top-3 Retrieval Limit

**Goal**: Verify no more than 3 memories are retrieved per query.

**Steps**:
```bash
SESSION_ID="test-top3"

# Store 5 different preferences (need 5 different audio files)
for i in {1..5}; do
  curl -X POST http://localhost:3000/converse \
    -F "audio=@preference-$i.wav" \
    -F "sessionId=$SESSION_ID" \
    -o store-$i.wav \
    -s
done

# Query for memories
curl -X POST http://localhost:3000/converse \
  -F "audio=@recall-all.wav" \
  -F "sessionId=$SESSION_ID" \
  -o recall-top3.wav
```

**Expected**:
- Server logs: `[Memory] Retrieved: 3 memories` (maximum)
- Only the 3 most relevant memories are injected into context

---

### 6. Persistence

#### Test 6.1: Memories Survive Server Restart

**Goal**: Verify Chroma memories persist across server restarts.

**Steps**:
```bash
SESSION_ID="test-persistence"

# 1. Store a memory
curl -X POST http://localhost:3000/converse \
  -F "audio=@preference.wav" \
  -F "sessionId=$SESSION_ID" \
  -o before-restart.wav

# 2. Stop the server
# Press Ctrl+C in the terminal running npm start

# 3. Restart the server
npm start

# 4. Wait for Chroma to initialize (~10 seconds)

# 5. Query the memory (same session ID)
curl -X POST http://localhost:3000/converse \
  -F "audio=@recall.wav" \
  -F "sessionId=$SESSION_ID" \
  -o after-restart.wav
```

**Expected**:
- Server initializes Chroma: `[Memory] Chroma initialized successfully`
- Memory is retrieved: `[Memory] Retrieved: 1 memories`
- Audio response includes the stored preference
- **Note**: Conversation buffer (10 turns) will be lost, but durable memories persist

---

### 7. Session ID Handling

#### Test 7.1: Auto-Generated Session ID

**Goal**: Verify the server generates a session ID if none is provided.

**Steps**:
```bash
# No sessionId field
curl -X POST http://localhost:3000/converse \
  -F "audio=@test2.wav" \
  -v \
  -o auto-session.wav 2>&1 | grep -i "x-session-id"
```

**Expected**:
- HTTP 200
- Response header includes: `X-Session-ID: session_<uuid>`
- Server logs: `[Memory] Generated new session ID: session_<uuid>`

---

#### Test 7.2: Session ID via Header

**Goal**: Verify session ID can be passed via header instead of form field.

**Steps**:
```bash
curl -X POST http://localhost:3000/converse \
  -H "X-Session-ID: header-test-session" \
  -F "audio=@test2.wav" \
  -o header-session.wav
```

**Expected**:
- HTTP 200
- Server logs: `[Memory] Using session ID: header-test-session`
- Session is created/used with the provided ID

---

### 8. Error Handling

#### Test 8.1: Missing Audio File

**Steps**:
```bash
curl -X POST http://localhost:3000/converse \
  -F "sessionId=error-test" \
  -v
```

**Expected**:
- HTTP 400
- Error: "No audio file provided"

---

#### Test 8.2: Empty/Silent Audio

**Requirement**: An audio file with silence or no speech

**Steps**:
```bash
curl -X POST http://localhost:3000/converse \
  -F "audio=@silent.wav" \
  -F "sessionId=error-test" \
  -v
```

**Expected**:
- HTTP 400 or successful transcription with empty result
- Error: "No speech detected in audio"

---

## Automated Test Script

Use the provided test script for basic automated testing:

```bash
./test-phase2.sh
```

This script tests:
- New session creation
- Conversation history within a session
- Session isolation between different sessions
- Auto-generated session IDs

---

## Monitoring Memory Operations

### Server Log Format

Watch for these log patterns:

**Session Management**:
```
[Memory] Session: <sessionId> - New session created
[Memory] Using session ID: <sessionId>
[Memory] Generated new session ID: <sessionId>
```

**Memory Retrieval**:
```
[Memory] Session: <sessionId> - Retrieved: X memories
[Memory] Session: <sessionId> - No memories found
```

**Memory Extraction**:
```
[Memory] Extracting durable memory...
[Memory] Extracted durable fact: "<fact>"
[Memory] Stored memory: mem_<uuid> for session <sessionId>
```

**Rolling Buffer**:
```
[Memory] Session: <sessionId> - Removed oldest turn, kept last 10
```

**Initialization**:
```
[Memory] Loading embedding model...
[Memory] Embedding model loaded
[Memory] Chroma initialized successfully
```

---

## Inspecting Chroma Data

Chroma data is stored in: `./data/chroma/`

To verify memories are persisted:

```bash
# Check if Chroma directory exists
ls -la data/chroma/

# See stored data
find data/chroma -type f
```

**Note**: Chroma uses a binary format, so files are not human-readable.

---

## Performance Considerations

### Expected Response Times

- **First request** (cold start): ~15-25 seconds
  - Embedding model loading: ~10 seconds
  - Chroma initialization: ~2-5 seconds
  - Normal pipeline: ~3-10 seconds

- **Subsequent requests**: ~3-10 seconds
  - STT: ~1-2 seconds
  - Embedding + retrieval: ~0.5-1 second
  - Gemini: ~1-3 seconds
  - Memory extraction (background): ~1-2 seconds
  - TTS: ~1-3 seconds

### Memory Extraction is Non-Blocking

The memory extraction happens asynchronously using `setImmediate()`, so it doesn't delay the audio response. The flow is:

1. Get transcript
2. Retrieve memories
3. Generate response
4. **Return audio immediately**
5. Extract memory in background
6. Store if needed

---

## Troubleshooting

### Issue: "No memories found" when they should exist

**Possible causes**:
- Wrong session ID
- Chroma not initialized
- Embeddings not matching (different model version)

**Debug**:
```bash
# Check Chroma data exists
ls -la data/chroma/

# Restart server to reinitialize Chroma
npm start

# Verify correct session ID in logs
```

---

### Issue: Memory extraction not happening

**Possible causes**:
- Memory extraction running in background failed silently
- Gemini API rate limit
- User message doesn't contain memorable content

**Debug**:
- Watch server logs for `[Memory] Background memory extraction failed:`
- Check Gemini API status
- Try with an explicit preference statement

---

### Issue: Rolling buffer not rolling

**Possible causes**:
- Not using the same session ID across requests
- Server restarted (session memory is in-memory only)

**Debug**:
- Verify session ID is consistent in logs
- Count turns: should see "Removed oldest turn" on turn 11

---

### Issue: Sessions leaking between users

**Check**:
- Each request should use a unique session ID per user
- Server logs should show separate session IDs
- Memory retrieval should only show memories for current session

**Verify**:
```bash
# Create session A with specific memory
# Query from session B
# Session B should NOT see session A's memories
```

---

## Summary Checklist

- [ ] New session creation works
- [ ] Conversation history retained within session
- [ ] Rolling 10-turn buffer functions correctly
- [ ] Session isolation verified
- [ ] Durable memories extracted from preferences
- [ ] Non-memorable content not stored
- [ ] Memories retrieved and used in responses
- [ ] Top-3 retrieval limit enforced
- [ ] Memories persist after server restart
- [ ] Auto-generated session IDs work
- [ ] Session ID via header works
- [ ] Error handling for missing audio
- [ ] Performance is acceptable

---

## Need Help?

Check:
1. Server logs for detailed error messages
2. `/health` endpoint for service status
3. README.md for architecture overview
4. Ensure all Phase 1 tests pass before testing Phase 2
