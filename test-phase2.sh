#!/bin/bash

# Phase 2 Memory Testing Script
# Tests session-based conversation memory, rolling buffer, and Chroma persistence

set -e

BASE_URL="http://localhost:3000"
TEST_AUDIO="test2.wav"
SESSION_A="test-session-a"
SESSION_B="test-session-b"

echo "=========================================="
echo "Phase 2: Conversation Memory Testing"
echo "=========================================="
echo ""

# Check if server is running
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
  echo "❌ Server is not running!"
  echo "   Start it with: npm start"
  exit 1
fi

echo "✅ Server is running"
echo ""

# Test 1: New session with no previous memory
echo "TEST 1: New session (no previous memory)"
echo "Session: $SESSION_A"
echo "Expected: Assistant responds normally with no context"
echo ""
curl -X POST "$BASE_URL/converse" \
  -F "audio=@$TEST_AUDIO" \
  -F "sessionId=$SESSION_A" \
  -o test-response-1.wav \
  -s -w "HTTP Status: %{http_code}\n"
echo "Response saved to: test-response-1.wav"
echo ""

# Test 2: Same session - conversation history should be retained
echo "TEST 2: Second request in same session"
echo "Session: $SESSION_A"
echo "Expected: Assistant has access to turn 1 in conversation history"
echo ""
curl -X POST "$BASE_URL/converse" \
  -F "audio=@$TEST_AUDIO" \
  -F "sessionId=$SESSION_A" \
  -o test-response-2.wav \
  -s -w "HTTP Status: %{http_code}\n"
echo "Response saved to: test-response-2.wav"
echo ""

# Test 3: Different session - should NOT have Session A's history
echo "TEST 3: Different session (session isolation)"
echo "Session: $SESSION_B"
echo "Expected: No access to Session A's conversation history"
echo ""
curl -X POST "$BASE_URL/converse" \
  -F "audio=@$TEST_AUDIO" \
  -F "sessionId=$SESSION_B" \
  -o test-response-3.wav \
  -s -w "HTTP Status: %{http_code}\n"
echo "Response saved to: test-response-3.wav"
echo ""

# Test 4: No session ID provided - should generate one
echo "TEST 4: No session ID (auto-generation)"
echo "Expected: Server generates and returns session ID in X-Session-ID header"
echo ""
RESPONSE=$(curl -X POST "$BASE_URL/converse" \
  -F "audio=@$TEST_AUDIO" \
  -o test-response-4.wav \
  -s -D - \
  -w "\nHTTP Status: %{http_code}\n")
echo "$RESPONSE" | grep -i "x-session-id" || echo "⚠️  X-Session-ID header not found"
echo "Response saved to: test-response-4.wav"
echo ""

echo "=========================================="
echo "Manual Testing Instructions"
echo "=========================================="
echo ""
echo "To test durable memory extraction and retrieval:"
echo ""
echo "1. Start a new session and state a preference:"
echo '   curl -X POST "$BASE_URL/converse" \'
echo '     -F "audio=@<audio_saying_I_prefer_dark_mode.wav>" \'
echo '     -F "sessionId=memory-test" \'
echo '     -o response.wav'
echo ""
echo "2. Check server logs for:"
echo "   [Memory] Extracted durable fact: ..."
echo "   [Memory] Stored memory: ..."
echo ""
echo "3. Ask a related question:"
echo '   curl -X POST "$BASE_URL/converse" \'
echo '     -F "audio=@<audio_asking_what_do_I_prefer.wav>" \'
echo '     -F "sessionId=memory-test" \'
echo '     -o response2.wav'
echo ""
echo "4. Check server logs for:"
echo "   [Memory] Retrieved: X memories"
echo ""
echo "To test rolling 10-turn buffer:"
echo "- Send 11+ requests with the same sessionId"
echo "- Server logs should show: 'Removed oldest turn, kept last 10'"
echo ""
echo "To test persistence:"
echo "- Store a memory"
echo "- Restart server: npm start"
echo "- Query with same sessionId"
echo "- Memory should still be retrieved"
echo ""
echo "Chroma data location: ./data/chroma/"
echo ""
