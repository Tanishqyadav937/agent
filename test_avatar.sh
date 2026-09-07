#!/bin/bash

echo "=========================================="
echo "AVATAR SYSTEM - END-TO-END TEST"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_count=0
pass_count=0

function test_case() {
    test_count=$((test_count + 1))
    echo ""
    echo "[$test_count] $1"
}

function pass() {
    pass_count=$((pass_count + 1))
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

function fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
}

# Test 1: Backend running
test_case "Backend Health Check"
HEALTH=$(curl -s http://localhost:3000/health)
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    pass "Backend running (HTTP 200, status=ok)"
else
    fail "Backend not responding correctly"
    exit 1
fi

# Test 2: avatar.html accessible
test_case "avatar.html Static File"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/avatar.html)
if [ "$HTTP_CODE" = "200" ]; then
    pass "avatar.html accessible (HTTP 200)"
else
    fail "avatar.html returned HTTP $HTTP_CODE"
fi

# Test 3: GLB file accessible
test_case "GLB File Serving"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/bunny_character_lipsync.glb)
GLB_SIZE=$(curl -s -I http://localhost:3000/bunny_character_lipsync.glb | grep Content-Length | awk '{print $2}')
if [ "$HTTP_CODE" = "200" ] && [ ! -z "$GLB_SIZE" ]; then
    pass "GLB accessible (HTTP 200, ${GLB_SIZE} bytes)"
else
    fail "GLB not accessible"
fi

# Test 4: /converse endpoint (original, unchanged)
test_case "/converse Endpoint (Audio API)"
# Create a small test audio file (silence, 44.1kHz, 16-bit, 1 channel, 0.5s)
python3 << 'EOF'
import wave
import os

output_path = '/tmp/test_silence.wav'
sample_rate = 44100
duration = 0.5
num_samples = int(sample_rate * duration)

with wave.open(output_path, 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(b'\x00\x00' * num_samples)
EOF

RESPONSE=$(curl -s -w "\n%{http_code}" -F "audio=@/tmp/test_silence.wav" http://localhost:3000/converse)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "200" ]; then
    pass "/converse returns HTTP 200 (audio API working)"
else
    fail "/converse returned HTTP $HTTP_CODE"
fi

# Test 5: Ollama model status
test_case "Ollama Model Availability"
if echo "$HEALTH" | grep -q '"model_available":true'; then
    MODEL_NAME=$(echo "$HEALTH" | grep -o '"model_name":"[^"]*' | cut -d'"' -f4)
    pass "Ollama model available: $MODEL_NAME"
else
    fail "Ollama model not available"
fi

# Test 6: Piper TTS
test_case "Piper TTS Service"
if echo "$HEALTH" | grep -q '"piper":true'; then
    pass "Piper TTS available"
else
    fail "Piper TTS not available"
fi

# Test 7: Chroma memory
test_case "Chroma Vector Store"
if echo "$HEALTH" | grep -q '"chroma":true'; then
    pass "Chroma initialized"
else
    fail "Chroma not initialized"
fi

# Test 8: Deepgram STT
test_case "Deepgram STT API Key"
if echo "$HEALTH" | grep -q '"deepgram":true'; then
    pass "Deepgram API key configured"
else
    fail "Deepgram not configured"
fi

# Test 9: Check avatar.html content
test_case "avatar.html Content Verification"
AVATAR_HTML=$(curl -s http://localhost:3000/avatar.html)
CHECKS=(
    "Three.js imports"
    "GLTFLoader"
    "Web Audio API"
    "getUserMedia"
    "morphTargetInfluences"
    "jawOpen"
    "viseme_"
)
MISSING=()
for check in "${CHECKS[@]}"; do
    if ! echo "$AVATAR_HTML" | grep -q "$check"; then
        MISSING+=("$check")
    fi
done

if [ ${#MISSING[@]} -eq 0 ]; then
    pass "All required components found in avatar.html"
else
    fail "Missing components: ${MISSING[*]}"
fi

# Test 10: Files exist
test_case "File Verification"
if [ -f "/Users/tanishqyadav/agent/avatar.html" ] && \
   [ -f "/Users/tanishqyadav/agent/bunny_character_lipsync.glb" ] && \
   [ -f "/Users/tanishqyadav/agent/server.js" ]; then
    pass "All required files exist"
else
    fail "Some files missing"
fi

# Test 11: Test /converse with actual message
test_case "/converse Response Content"
RESPONSE=$(curl -s -F "audio=@/tmp/test_silence.wav" http://localhost:3000/converse)
# Check if response is audio (starts with RIFF header for WAV)
if echo "$RESPONSE" | head -c 4 | grep -q "RIFF"; then
    pass "/converse returns WAV audio data"
else
    echo "Response preview (first 100 bytes):"
    echo "$RESPONSE" | head -c 100 | od -c | head -5
    fail "/converse response is not valid audio"
fi

# Summary
echo ""
echo "=========================================="
echo -e "RESULTS: ${GREEN}$pass_count/$test_count${NC} tests passed"
echo "=========================================="

if [ $pass_count -eq $test_count ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "To test in browser:"
    echo "  1. Open: http://localhost:3000/avatar.html"
    echo "  2. Click '🎤 Start Recording'"
    echo "  3. Speak into the microphone"
    echo "  4. Click '⏹️ Stop Recording'"
    echo "  5. Wait for response and observe:"
    echo "     - Avatar mouth opens (jawOpen)"
    echo "     - Visemes animate (A/E/I/O/U)"
    echo "     - Eyes blink during idle"
    echo "     - Status changes (idle → listening → speaking)"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
