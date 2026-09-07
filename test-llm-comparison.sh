#!/bin/bash

# LLM Comparison Test Script
# Compares Ollama (local) vs Gemini (cloud) responses

echo "=========================================="
echo "LLM Provider Comparison Test"
echo "=========================================="
echo ""

# Test prompt
TEST_PROMPT="Tell me a very short joke suitable for a voice assistant."

echo "Test prompt: \"$TEST_PROMPT\""
echo ""

# Test Ollama
echo "-------------------------------------------"
echo "1. Testing Ollama (local - llama3.2)"
echo "-------------------------------------------"
echo ""

OLLAMA_START=$(date +%s)
OLLAMA_RESPONSE=$(curl -s http://localhost:11434/api/chat -d "{
  \"model\": \"llama3.2\",
  \"messages\": [
    {\"role\": \"system\", \"content\": \"You are a helpful voice assistant. Keep responses concise and conversational.\"},
    {\"role\": \"user\", \"content\": \"$TEST_PROMPT\"}
  ],
  \"stream\": false
}" | jq -r '.message.content')
OLLAMA_END=$(date +%s)
OLLAMA_TIME=$((OLLAMA_END - OLLAMA_START))

echo "Response: $OLLAMA_RESPONSE"
echo ""
echo "Time: ${OLLAMA_TIME}s"
echo ""

# Test Gemini (if API key is available)
echo "-------------------------------------------"
echo "2. Testing Gemini (cloud)"
echo "-------------------------------------------"
echo ""

if grep -q "^GEMINI_API_KEY=.*[^example]" ~/.agent/.env 2>/dev/null || grep -q "^GEMINI_API_KEY=.*[^example]" ~/agent/.env 2>/dev/null; then
  echo "✅ Gemini API key found"
  echo ""
  echo "To test Gemini:"
  echo "1. Edit .env and set: LLM_PROVIDER=cloud"
  echo "2. Start server: npm start"
  echo "3. Make a request and observe response quality"
  echo ""
else
  echo "⚠️  Gemini API key not configured"
  echo "   Cannot test cloud provider"
  echo ""
fi

echo "=========================================="
echo "Quality Assessment Checklist"
echo "=========================================="
echo ""
echo "For Ollama response above, evaluate:"
echo ""
echo "[ ] Natural and conversational?"
echo "[ ] Appropriate length (2-3 sentences)?"
echo "[ ] Suitable for voice output?"
echo "[ ] Relevant to the prompt?"
echo "[ ] Response time acceptable (< 10s)?"
echo ""
echo "If all criteria are met, Ollama quality is acceptable."
echo "If not, consider switching to Gemini with:"
echo "  LLM_PROVIDER=cloud in .env"
echo ""
