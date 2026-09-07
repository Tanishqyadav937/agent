#!/bin/bash

# Test script for voice assistant API using curl
# 
# Usage:
#   ./test-curl.sh <audio-file-path>
#
# Example:
#   ./test-curl.sh recording.wav

if [ -z "$1" ]; then
  echo "Usage: ./test-curl.sh <audio-file-path>"
  echo "Example: ./test-curl.sh recording.wav"
  exit 1
fi

AUDIO_FILE="$1"
OUTPUT_FILE="response.wav"
API_URL="${API_URL:-http://localhost:3000/converse}"

if [ ! -f "$AUDIO_FILE" ]; then
  echo "❌ Error: File not found: $AUDIO_FILE"
  exit 1
fi

echo "🎤 Testing voice assistant..."
echo "📁 Input: $AUDIO_FILE"
echo "📡 API: $API_URL"
echo ""

# Send request and measure time
echo "⏳ Sending request..."
START=$(date +%s)

HTTP_CODE=$(curl -X POST "$API_URL" \
  -F "audio=@$AUDIO_FILE" \
  -w "%{http_code}" \
  -o "$OUTPUT_FILE" \
  -s)

END=$(date +%s)
DURATION=$((END - START))

echo ""

if [ "$HTTP_CODE" -eq 200 ]; then
  FILE_SIZE=$(wc -c < "$OUTPUT_FILE" | tr -d ' ')
  echo "✅ Success! (${DURATION}s)"
  echo "🔊 Response saved to: $OUTPUT_FILE"
  echo "📊 Response size: $FILE_SIZE bytes"
  echo ""
  echo "Play with: afplay $OUTPUT_FILE"
else
  echo "❌ Error: HTTP $HTTP_CODE"
  cat "$OUTPUT_FILE"
  echo ""
  exit 1
fi
