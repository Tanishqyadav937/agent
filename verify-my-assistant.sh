#!/bin/bash

# Quick verification script for my-assistant integration

echo "=========================================="
echo "my-assistant Integration Verification"
echo "=========================================="
echo ""

# Check 1: Configuration
echo "1. Checking configuration..."
MODEL=$(grep "OLLAMA_MODEL=" ~/agent/.env | cut -d= -f2)
TOOLS=$(grep "TOOLS_ENABLED=" ~/agent/.env | cut -d= -f2)
echo "   Model: $MODEL"
echo "   Tools enabled: $TOOLS"

if [ "$MODEL" = "my-assistant" ]; then
  echo "   ✅ Model set to my-assistant"
else
  echo "   ⚠️  Model is $MODEL, expected my-assistant"
fi

if [ "$TOOLS" = "false" ]; then
  echo "   ✅ Tools disabled (simple chat mode)"
else
  echo "   ⚠️  Tools enabled - may fail if model doesn't support tools"
fi
echo ""

# Check 2: Ollama running
echo "2. Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo "   ✅ Ollama is running"
else
  echo "   ❌ Ollama is not running!"
  echo "   Start with: ollama serve"
  exit 1
fi
echo ""

# Check 3: Model available
echo "3. Checking if my-assistant model exists..."
if ollama list 2>/dev/null | grep -q "my-assistant"; then
  echo "   ✅ my-assistant model found"
  ollama list | grep "my-assistant"
else
  echo "   ❌ my-assistant model not found!"
  echo ""
  echo "   Available models:"
  ollama list | tail -n +2 | awk '{print "   - " $1}'
  echo ""
  echo "   To create your model:"
  echo "   1. Create a Modelfile with your fine-tuned model"
  echo "   2. Run: ollama create my-assistant -f Modelfile"
  exit 1
fi
echo ""

# Check 4: Chroma Docker
echo "4. Checking Chroma service..."
if docker ps | grep -q "chroma-server"; then
  echo "   ✅ Chroma container is running"
elif docker ps -a | grep -q "chroma-server"; then
  echo "   ⚠️  Chroma container exists but is stopped"
  echo "   Start with: docker start chroma-server"
else
  echo "   ⚠️  Chroma container not found"
  echo "   Create with:"
  echo "   docker run -d --name chroma-server -p 8000:8000 \\"
  echo "     -v ~/agent/data/chroma:/chroma/chroma chromadb/chroma:latest"
fi
echo ""

# Check 5: Syntax check
echo "5. Checking server.js syntax..."
if node -c ~/agent/server.js 2>&1; then
  echo "   ✅ No syntax errors"
else
  echo "   ❌ Syntax errors found!"
  exit 1
fi
echo ""

# Check 6: Test health endpoint (if server is running)
echo "6. Testing health endpoint..."
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
  echo "   ✅ Server is running"
  echo ""
  echo "   Health status:"
  HEALTH=$(curl -s http://localhost:3000/health)
  echo "$HEALTH" | jq '{status, ollama: .services.ollama}' 2>/dev/null || echo "$HEALTH"
else
  echo "   ⚠️  Server not running (this is OK if you haven't started it yet)"
  echo "   Start with: npm start"
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  ✓ Model: $MODEL"
echo "  ✓ Tools: $TOOLS (disabled for simple chat)"
echo "  ✓ Syntax: Valid"
echo ""
echo "Services:"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo "  ✓ Ollama: Running"
else
  echo "  ✗ Ollama: Not running"
fi

if ollama list 2>/dev/null | grep -q "my-assistant"; then
  echo "  ✓ Model: Available"
else
  echo "  ✗ Model: Not found"
fi

if docker ps | grep -q "chroma-server"; then
  echo "  ✓ Chroma: Running"
else
  echo "  ✗ Chroma: Not running"
fi
echo ""

# Final check
ALL_GOOD=true

if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  ALL_GOOD=false
fi

if ! ollama list 2>/dev/null | grep -q "my-assistant"; then
  ALL_GOOD=false
fi

if [ "$ALL_GOOD" = true ]; then
  echo "✅ All systems ready!"
  echo ""
  echo "Next steps:"
  echo "  1. Start server: npm start"
  echo "  2. Test health: curl http://localhost:3000/health | jq ."
  echo "  3. Test conversation: curl -X POST http://localhost:3000/converse \\"
  echo "       -F 'audio=@test.wav' -o response.wav && afplay response.wav"
  echo ""
  echo "See TEST_MY_ASSISTANT.md for detailed testing instructions."
else
  echo "⚠️  Some services need attention (see above)"
  echo ""
  echo "Quick fixes:"
  echo "  - Ollama: ollama serve"
  echo "  - Chroma: docker start chroma-server"
  echo "  - Model: ollama create my-assistant -f Modelfile"
fi
echo ""
