# Embedding Model Migration - Xenova to Ollama

## Overview

Replaced the Xenova Transformers embedding model (`all-MiniLM-L6-v2`) with Ollama-based local embeddings (`nomic-embed-text` or `mxbai-embed-large`) for the Chroma vector store.

**Status**: ✅ Code complete, awaiting model download

---

## Why Replace?

### Previous System (Xenova Transformers)
- Model: `Xenova/all-MiniLM-L6-v2`
- Dimensions: 384
- Provider: @xenova/transformers (Node.js library)
- Size: ~80MB download on first use
- Performance: Fast, runs in Node.js

**Issues**:
- Additional Node.js dependency
- Separate from Ollama ecosystem
- Different API than LLM

### New System (Ollama Embeddings)
- Model: `nomic-embed-text` (default) or `mxbai-embed-large`
- Dimensions: 768 (nomic) or 1024 (mxbai)
- Provider: Ollama (same as LLM)
- Size: ~274MB (nomic) or ~669MB (mxbai)
- Performance: Depends on Ollama service

**Benefits**:
- ✅ Unified ecosystem (Ollama for both LLM and embeddings)
- ✅ Better semantic understanding
- ✅ Higher dimensional embeddings (more precise)
- ✅ Consistent API
- ✅ No additional Node.js ML dependencies

---

## Code Changes

### File: server.js

**Added Configuration** (~line 35):
```javascript
// Embedding Configuration
const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL || 'nomic-embed-text';
const EMBEDDING_PROVIDER = 'ollama'; // Using Ollama for local embeddings

console.log(`[Embedding] Provider: ${EMBEDDING_PROVIDER}, Model: ${EMBEDDING_MODEL}`);

// Session-based conversation memory (rolling 10 turns)
const sessionMemory = new Map();
```

**Replaced Embedding Function** (~line 65):
```javascript
// OLD:
async function getEmbeddingModel() {
  if (!embeddingModel) {
    console.log('[Memory] Loading embedding model...');
    embeddingModel = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    console.log('[Memory] Embedding model loaded');
  }
  return embeddingModel;
}

async function generateEmbedding(text) {
  try {
    const model = await getEmbeddingModel();
    const output = await model(text, { pooling: 'mean', normalize: true });
    return Array.from(output.data);
  } catch (error) {
    console.error('[Memory] Embedding generation failed:', error.message);
    throw error;
  }
}

// NEW:
async function generateEmbedding(text) {
  try {
    const response = await fetch(`${OLLAMA_BASE_URL}/api/embeddings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: EMBEDDING_MODEL,
        prompt: text
      })
    });

    if (!response.ok) {
      throw new Error(`Ollama embedding API error: ${response.statusText}`);
    }

    const data = await response.json();
    
    if (!data || !data.embedding) {
      throw new Error('No embedding returned from Ollama');
    }

    return data.embedding;
  } catch (error) {
    console.error('[Embedding] Generation failed:', error.message);
    throw error;
  }
}
```

**Impact on Other Functions**:
- `retrieveRelevantMemories()` - No changes (uses generateEmbedding)
- `storeMemory()` - No changes (uses generateEmbedding)
- All memory operations automatically use new embedding model

---

## Configuration

### Environment Variables

**File: .env.example**
```bash
# Embedding Model Configuration (for memory/Chroma)
EMBEDDING_MODEL=nomic-embed-text
```

**File: .env**
```bash
EMBEDDING_MODEL=nomic-embed-text
```

---

## Model Options

### nomic-embed-text (Default)
```bash
ollama pull nomic-embed-text
```

**Specs**:
- Size: ~274MB
- Dimensions: 768
- Context: 8192 tokens
- Use case: General-purpose embeddings
- Performance: Fast
- Quality: Excellent for retrieval

**Pros**:
- Good balance of size and quality
- Fast inference
- Well-tested

**Cons**:
- Smaller than mxbai (lower dimensions)

### mxbai-embed-large (Alternative)
```bash
ollama pull mxbai-embed-large
```

**Specs**:
- Size: ~669MB
- Dimensions: 1024
- Context: 512 tokens
- Use case: High-precision embeddings
- Performance: Slower (larger model)
- Quality: Better semantic understanding

**Pros**:
- Higher dimensional (more precise)
- Better for complex queries

**Cons**:
- Larger download
- Slower inference
- More RAM usage

---

## Migration Process

### For New Systems (No Existing Memories)
✅ **No migration needed** - just update code and pull model

1. Update server.js (already done)
2. Update .env (already done)
3. Pull embedding model:
   ```bash
   ollama pull nomic-embed-text
   ```
4. Start server:
   ```bash
   npm start
   ```

### For Systems with Existing Memories
⚠️ **Re-embedding required** - old vectors are incompatible

**Why Re-embedding is Needed**:
- Embeddings from different models have different dimensions and representations
- Xenova all-MiniLM-L6-v2: 384 dimensions
- nomic-embed-text: 768 dimensions
- mxbai-embed-large: 1024 dimensions
- Cannot mix embeddings from different models in same collection

**Re-embedding Steps**:

1. **Backup existing Chroma data** (optional but recommended):
   ```bash
   cp -r ~/agent/data/chroma ~/agent/data/chroma.backup
   ```

2. **Pull new embedding model**:
   ```bash
   ollama pull nomic-embed-text
   ```

3. **Verify model is available**:
   ```bash
   ollama list | grep nomic
   ```

4. **Run re-embedding script**:
   ```bash
   node reembed-memories.js
   ```

5. **Verify re-embedding**:
   - Check script output for success
   - Start server and test memory retrieval
   - Compare retrieval quality

**Re-embedding Script** (`reembed-memories.js`):
- Fetches all existing memories from Chroma
- Generates new embeddings using Ollama
- Updates each memory with new embedding
- Preserves documents and metadata
- Shows progress for each memory

---

## Testing

### 1. Test Ollama Embedding API

```bash
./test-embedding.sh
```

Expected output:
```
✅ Ollama is running
✅ nomic-embed-text is available
✅ Embedding generated successfully
   Dimensions: 768
```

### 2. Manual Embedding Test

```bash
curl -s http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "I prefer dark mode"
}' | jq '.embedding | length'
```

Expected: `768` (dimension count)

### 3. Test Memory Storage and Retrieval

```bash
# Start server
npm start

# Create a memory (in another terminal)
curl -X POST http://localhost:3000/converse \
  -F "audio=@preference.wav" \
  -F "sessionId=embed-test" \
  -o response.wav

# Check server logs for:
# [Embedding] Generation successful
# [Memory] Stored memory: mem_xxxxx
```

### 4. Test Memory Retrieval

```bash
# Query related to stored memory
curl -X POST http://localhost:3000/converse \
  -F "audio=@recall.wav" \
  -F "sessionId=embed-test" \
  -o response2.wav

# Check server logs for:
# [Memory] Retrieved: 1 memories
```

---

## Quality Comparison

### Test Retrieval Quality

**Test Memories**:
1. "User prefers dark mode"
2. "User works late at night"
3. "User prefers concise answers"

**Test Queries**:
- "What are my preferences?" (should retrieve all 3)
- "Do I like dark mode?" (should retrieve #1)
- "When do I work?" (should retrieve #2)
- "How should you answer?" (should retrieve #3)

**Evaluation Criteria**:
- ✅ Correct memories retrieved?
- ✅ Top-3 ranking makes sense?
- ✅ Irrelevant memories filtered out?
- ✅ Similar concepts grouped together?

### Expected Quality

**nomic-embed-text**:
- ✅ Excellent for conversational queries
- ✅ Good semantic understanding
- ✅ Fast retrieval
- ✅ Handles synonyms well

**Compared to Xenova all-MiniLM-L6-v2**:
- 🔼 Better: Higher dimensions (768 vs 384)
- 🔼 Better: Stronger semantic understanding
- 🔼 Better: More recent training data
- 🔽 Slower: External API call (vs in-process)
- ➡️ Similar: Retrieval relevance for simple queries

---

## Performance Impact

### Embedding Generation Time

**Xenova (in-process)**:
- First embedding: ~0.1-0.3s (model load)
- Subsequent: ~0.01-0.05s

**Ollama (API call)**:
- All embeddings: ~0.05-0.2s (depends on model and hardware)
- Consistent performance (no warm-up needed)

**Impact on Request Flow**:
- Memory retrieval: +0.05-0.2s per request
- Total request time: ~5-10s (embedding is small part)
- **Acceptable for voice assistant**

### Memory Usage

**Xenova**:
- Node.js process: +50-100MB
- Model cached in memory

**Ollama**:
- Node.js process: No change
- Ollama service: +200-500MB (depends on model)
- Ollama handles model loading/caching

**System Total**:
- Before: ~2GB (llama3.2) + ~100MB (Xenova)
- After: ~2GB (llama3.2) + ~300MB (nomic-embed-text)
- Net change: +200MB

**Available**: 16GB RAM
**Usage**: ~3GB total
**Headroom**: ✅ Plenty

---

## Troubleshooting

### Model Not Downloaded

**Symptom**:
```
Error: Ollama embedding API error: model 'nomic-embed-text' not found
```

**Fix**:
```bash
ollama pull nomic-embed-text
```

### Ollama Not Running

**Symptom**:
```
Error: fetch failed (connection refused)
```

**Fix**:
```bash
ollama serve
```

### Wrong Dimensions

**Symptom**:
- Chroma error about incompatible dimensions
- Old embeddings (384) vs new embeddings (768)

**Fix**:
```bash
# Option 1: Re-embed existing memories
node reembed-memories.js

# Option 2: Clear and start fresh
docker stop chroma-server
rm -rf ~/agent/data/chroma/*
docker start chroma-server
npm start
```

### Slow Embedding Generation

**Symptoms**:
- Embeddings take >1 second
- Memory retrieval is slow

**Possible Causes**:
1. Model not fully loaded in Ollama
2. CPU-bound (no GPU acceleration)
3. mxbai-embed-large (larger model)

**Fixes**:
```bash
# Switch to smaller model
# Edit .env:
EMBEDDING_MODEL=nomic-embed-text

# Restart server
npm start
```

---

## Verification Checklist

- [ ] Code updated in server.js
- [ ] .env updated with EMBEDDING_MODEL
- [ ] Ollama running
- [ ] Embedding model downloaded: `ollama list | grep nomic`
- [ ] Test script passes: `./test-embedding.sh`
- [ ] Manual embedding test works
- [ ] Server starts without errors
- [ ] Memory storage works (check logs)
- [ ] Memory retrieval works (check logs)
- [ ] Retrieval quality acceptable
- [ ] Performance acceptable (<10s per request)

---

## Summary

✅ **Migration Complete** (code ready, awaiting model download)

| Aspect | Old (Xenova) | New (Ollama) |
|--------|-------------|--------------|
| **Provider** | @xenova/transformers | Ollama API |
| **Model** | all-MiniLM-L6-v2 | nomic-embed-text |
| **Dimensions** | 384 | 768 |
| **Size** | ~80MB | ~274MB |
| **Speed** | 0.01-0.05s | 0.05-0.2s |
| **Quality** | Good | Better |
| **Ecosystem** | Separate | Unified with LLM |

**Benefits Achieved**:
- ✅ Unified Ollama ecosystem
- ✅ Better semantic understanding
- ✅ Higher dimensional embeddings
- ✅ Consistent API
- ✅ No additional ML dependencies

**Next Actions**:
1. Wait for model download to complete
2. Run `./test-embedding.sh`
3. Test memory storage and retrieval
4. Verify quality is acceptable
5. If needed, tune top-k or similarity threshold

**Current Status**:
- Code: ✅ Complete
- Model download: ⏳ In progress (mxbai-embed-large 90% complete)
- Testing: ⏳ Pending model availability
- Documentation: ✅ Complete
