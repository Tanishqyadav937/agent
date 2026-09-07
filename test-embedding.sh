#!/bin/bash

# Test script for Ollama embedding integration

echo "=========================================="
echo "Ollama Embedding Test"
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

# Check if nomic-embed-text is available
echo "2. Checking embedding model availability..."
if ollama list | grep -q "nomic-embed-text"; then
  echo "✅ nomic-embed-text is available"
  ollama list | grep "nomic-embed-text"
elif ollama list | grep -q "mxbai-embed-large"; then
  echo "✅ mxbai-embed-large is available"
  ollama list | grep "mxbai-embed-large"
  echo "   Update .env to: EMBEDDING_MODEL=mxbai-embed-large"
else
  echo "❌ No embedding model found!"
  echo "   Download one with:"
  echo "   ollama pull nomic-embed-text"
  echo "   or"
  echo "   ollama pull mxbai-embed-large"
  exit 1
fi
echo ""

# Test embedding API directly
echo "3. Testing Ollama embedding API..."
MODEL=$(grep "EMBEDDING_MODEL=" ~/agent/.env 2>/dev/null | cut -d= -f2 || echo "nomic-embed-text")
echo "Using model: $MODEL"
echo ""

RESPONSE=$(curl -s http://localhost:11434/api/embeddings -d "{
  \"model\": \"$MODEL\",
  \"prompt\": \"I prefer dark mode\"
}")

if echo "$RESPONSE" | grep -q "embedding"; then
  EMBEDDING_DIM=$(echo "$RESPONSE" | jq '.embedding | length' 2>/dev/null)
  echo "✅ Embedding generated successfully"
  echo "   Dimensions: $EMBEDDING_DIM"
else
  echo "❌ Embedding generation failed"
  echo "   Response: $RESPONSE"
  exit 1
fi
echo ""

# Test similarity (basic check)
echo "4. Testing embedding similarity..."
RESPONSE1=$(curl -s http://localhost:11434/api/embeddings -d "{
  \"model\": \"$MODEL\",
  \"prompt\": \"I like pizza\"
}")

RESPONSE2=$(curl -s http://localhost:11434/api/embeddings -d "{
  \"model\": \"$MODEL\",
  \"prompt\": \"I love pizza\"
}")

RESPONSE3=$(curl -s http://localhost:11434/api/embeddings -d "{
  \"model\": \"$MODEL\",
  \"prompt\": \"The weather is sunny\"
}")

echo "✅ Generated 3 test embeddings"
echo "   Similar texts: 'I like pizza' vs 'I love pizza'"
echo "   Different text: 'The weather is sunny'"
echo ""

# Check .env configuration
echo "5. Checking .env configuration..."
if grep -q "EMBEDDING_MODEL=" ~/agent/.env 2>/dev/null; then
  MODEL_CFG=$(grep "EMBEDDING_MODEL=" ~/agent/.env | cut -d= -f2)
  echo "✅ EMBEDDING_MODEL=$MODEL_CFG"
else
  echo "⚠️  EMBEDDING_MODEL not set in .env"
  echo "   Add: EMBEDDING_MODEL=nomic-embed-text"
fi
echo ""

# Check if Chroma is running
echo "6. Checking Chroma status..."
if docker ps | grep -q chroma-server; then
  echo "✅ Chroma Docker container is running"
else
  echo "⚠️  Chroma container not running"
  echo "   Start it with: docker start chroma-server"
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Embedding System:"
echo "  Provider: Ollama (local)"
echo "  Model: $MODEL"
echo "  Dimensions: $EMBEDDING_DIM"
echo ""
echo "Previous System:"
echo "  Provider: Xenova Transformers"
echo "  Model: all-MiniLM-L6-v2"
echo "  Dimensions: 384"
echo ""
echo "⚠️  Important: Embeddings from different models are NOT compatible."
echo "   If you have existing memories, run:"
echo "   node reembed-memories.js"
echo ""
echo "Next Steps:"
echo "  1. Ensure embedding model is fully downloaded"
echo "  2. Start server: npm start"
echo "  3. Test memory creation and retrieval"
echo "  4. Compare retrieval quality with previous system"
echo ""
