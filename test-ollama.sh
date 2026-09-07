#!/bin/bash

# Test script for Ollama integration

echo "=========================================="
echo "Ollama Integration Test"
echo "=========================================="
echo ""

# Check if Ollama is running
echo "1. Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo "✅ Ollama is running"
else
  echo "❌ Ollama is not running!"
  echo "   Start it with: ollama serve"
  exit 1
fi
echo ""

# Check available models
echo "2. Available Ollama models:"
ollama list
echo ""

# Test Ollama API directly
echo "3. Testing Ollama API directly..."
RESPONSE=$(curl -s http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and conversational."},
    {"role": "user", "content": "Hello! How are you?"}
  ],
  "stream": false
}')

echo "Ollama Response:"
echo "$RESPONSE" | jq -r '.message.content' 2>/dev/null || echo "$RESPONSE"
echo ""

# Check .env configuration
echo "4. Checking .env configuration..."
if grep -q "LLM_PROVIDER=local" ~/agent/.env 2>/dev/null; then
  echo "✅ LLM_PROVIDER=local"
else
  echo "⚠️  LLM_PROVIDER not set to 'local' in .env"
fi

if grep -q "OLLAMA_MODEL=" ~/agent/.env 2>/dev/null; then
  MODEL=$(grep "OLLAMA_MODEL=" ~/agent/.env | cut -d= -f2)
  echo "✅ OLLAMA_MODEL=$MODEL"
else
  echo "⚠️  OLLAMA_MODEL not set in .env"
fi
echo ""

echo "=========================================="
echo "Configuration"
echo "=========================================="
echo ""
echo "To use Ollama (local):"
echo "  LLM_PROVIDER=local"
echo ""
echo "To use Gemini (cloud):"
echo "  LLM_PROVIDER=cloud"
echo ""
echo "Current model: $(grep OLLAMA_MODEL ~/agent/.env 2>/dev/null | cut -d= -f2 || echo 'Not set')"
echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Start the server:"
echo "   npm start"
echo ""
echo "2. Test with audio:"
echo "   curl -X POST http://localhost:3000/converse \\"
echo "     -F \"audio=@test2.wav\" \\"
echo "     -F \"sessionId=test-ollama\" \\"
echo "     -o response.wav"
echo ""
echo "3. To switch to cloud (Gemini):"
echo "   Edit .env and set: LLM_PROVIDER=cloud"
echo ""
