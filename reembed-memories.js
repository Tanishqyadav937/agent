/**
 * Re-embedding Script for Chroma Memories
 * 
 * This script re-embeds existing memories when switching embedding models.
 * Embeddings from different models are incompatible, so all vectors must be regenerated.
 * 
 * Usage:
 *   node reembed-memories.js
 * 
 * Environment Variables:
 *   OLLAMA_BASE_URL - Ollama API endpoint (default: http://localhost:11434)
 *   EMBEDDING_MODEL - Embedding model to use (default: nomic-embed-text)
 */

import { ChromaClient } from 'chromadb';
import dotenv from 'dotenv';

dotenv.config();

const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL || 'nomic-embed-text';
const CHROMA_URL = 'http://localhost:8000';

console.log('='.repeat(60));
console.log('Chroma Memory Re-embedding Script');
console.log('='.repeat(60));
console.log(`Ollama URL: ${OLLAMA_BASE_URL}`);
console.log(`Embedding Model: ${EMBEDDING_MODEL}`);
console.log(`Chroma URL: ${CHROMA_URL}`);
console.log('');

// Generate embedding using Ollama
async function generateEmbedding(text) {
  const response = await fetch(`${OLLAMA_BASE_URL}/api/embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      prompt: text
    })
  });

  if (!response.ok) {
    throw new Error(`Ollama API error: ${response.statusText}`);
  }

  const data = await response.json();
  if (!data || !data.embedding) {
    throw new Error('No embedding returned');
  }

  return data.embedding;
}

async function main() {
  try {
    // Connect to Chroma
    console.log('Connecting to Chroma...');
    const chromaClient = new ChromaClient({ path: CHROMA_URL });
    
    // Get the memories collection
    const collection = await chromaClient.getOrCreateCollection({
      name: 'user_memories',
      metadata: { description: 'Durable user facts and preferences' }
    });
    
    console.log('✅ Connected to Chroma collection: user_memories\n');
    
    // Get all memories
    console.log('Fetching existing memories...');
    const results = await collection.get();
    
    if (!results || !results.ids || results.ids.length === 0) {
      console.log('✅ No existing memories found. Nothing to re-embed.');
      console.log('   This is expected for a new system.');
      return;
    }
    
    const count = results.ids.length;
    console.log(`Found ${count} memories to re-embed\n`);
    
    // Re-embed each memory
    console.log('Re-embedding memories...');
    for (let i = 0; i < count; i++) {
      const id = results.ids[i];
      const document = results.documents[i];
      const metadata = results.metadatas[i];
      
      process.stdout.write(`  [${i + 1}/${count}] Re-embedding memory ${id}...`);
      
      try {
        // Generate new embedding
        const embedding = await generateEmbedding(document);
        
        // Update with new embedding
        await collection.update({
          ids: [id],
          embeddings: [embedding],
          documents: [document],
          metadatas: [metadata]
        });
        
        console.log(' ✅');
      } catch (error) {
        console.log(` ❌ ${error.message}`);
      }
    }
    
    console.log('');
    console.log('='.repeat(60));
    console.log(`✅ Re-embedding complete: ${count} memories processed`);
    console.log('='.repeat(60));
    
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error('\nTroubleshooting:');
    console.error('  1. Ensure Ollama is running: ollama serve');
    console.error(`  2. Ensure embedding model is available: ollama list | grep ${EMBEDDING_MODEL}`);
    console.error(`  3. If not available: ollama pull ${EMBEDDING_MODEL}`);
    console.error('  4. Ensure Chroma Docker container is running: docker ps | grep chroma');
    process.exit(1);
  }
}

main();
