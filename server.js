import express from 'express';
import cors from 'cors';
import multer from 'multer';
import { createClient } from '@deepgram/sdk';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { CloudClient } from 'chromadb';
import { v4 as uuidv4 } from 'uuid';
import dotenv from 'dotenv';
import fs from 'fs';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { TOOLS, executeTool } from './tools.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

// Enable CORS for avatar frontend
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174', 'http://localhost:8000', 'http://127.0.0.1:3000', 'http://127.0.0.1:8000'],
  credentials: true
}));

// Parse JSON request bodies
app.use(express.json());

// Initialize API clients
const deepgram = createClient(process.env.DEEPGRAM_API_KEY);
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// LLM Provider Configuration
// In production (Render), LLM_PROVIDER should be 'gemini' to skip Ollama entirely
// Possible values: 'local' (Ollama), 'gemini' (Google Gemini - production), 'cloud' (legacy, maps to gemini)
const LLM_PROVIDER = process.env.LLM_PROVIDER || 'local'; // 'local', 'gemini', or 'cloud'
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'llama3.2';
const TOOLS_ENABLED = process.env.TOOLS_ENABLED === 'true'; // Enable function calling

// Normalize provider names
const normalizedProvider = LLM_PROVIDER === 'cloud' ? 'gemini' : LLM_PROVIDER;

console.log(`[LLM] Provider: ${normalizedProvider}${normalizedProvider === 'local' ? ` (${OLLAMA_MODEL})` : ' (Google Gemini)'}`);
console.log(`[LLM] Tools enabled: ${TOOLS_ENABLED}`);
// Initialize Chroma Cloud client
const CHROMA_API_KEY = process.env.CHROMA_API_KEY;
const CHROMA_TENANT = process.env.CHROMA_TENANT;
const CHROMA_DATABASE = process.env.CHROMA_DATABASE;

console.log(`[Chroma] Initializing Cloud Client${CHROMA_API_KEY ? ' (with API key)' : ' (no API key - will fail)'}`);

let chromaClient;
if (CHROMA_API_KEY && CHROMA_TENANT && CHROMA_DATABASE) {
  // Chroma Cloud with explicit credentials
  chromaClient = new CloudClient({
    apiKey: CHROMA_API_KEY,
    tenant: CHROMA_TENANT,
    database: CHROMA_DATABASE
  });
} else {
  console.warn('[Chroma] Warning: Missing required Chroma Cloud credentials');
  console.warn('[Chroma] Required: CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE');
  chromaClient = null;
}

// Embedding Configuration
const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL || 'nomic-embed-text';
const EMBEDDING_PROVIDER = 'ollama'; // Using Ollama for local embeddings

console.log(`[Embedding] Provider: ${EMBEDDING_PROVIDER}, Model: ${EMBEDDING_MODEL}`);

// Session-based conversation memory (rolling 10 turns)
const sessionMemory = new Map();

// System prompt defining assistant personality
const SYSTEM_PROMPT = `You are a helpful and friendly voice assistant. Keep your responses concise and conversational, as they will be spoken aloud. Aim for responses that are 2-3 sentences unless more detail is specifically requested.`;

// Initialize Chroma collection
let memoryCollection = null;

async function initializeChroma() {
  try {
    // Get or create collection for user memories
    memoryCollection = await chromaClient.getOrCreateCollection({
      name: 'user_memories',
      metadata: { description: 'Durable user facts and preferences' }
    });
    
    console.log('[Memory] Chroma initialized successfully');
  } catch (error) {
    console.warn('[Memory] Chroma server not reachable. Running without persistent memory:', error.message);
    memoryCollection = null;
  }
}

// Generate embedding using Ollama
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

// Get or create session
function getSession(sessionId) {
  if (!sessionMemory.has(sessionId)) {
    sessionMemory.set(sessionId, {
      turns: [],
      createdAt: Date.now()
    });
    console.log(`[Memory] Session: ${sessionId} - New session created`);
  }
  return sessionMemory.get(sessionId);
}

// Add turn to session (rolling 10 turns)
function addTurnToSession(sessionId, userMessage, assistantReply) {
  const session = getSession(sessionId);
  session.turns.push({ user: userMessage, assistant: assistantReply });
  
  // Keep only last 10 turns
  if (session.turns.length > 10) {
    session.turns.shift();
    console.log(`[Memory] Session: ${sessionId} - Removed oldest turn, kept last 10`);
  }
}

// Retrieve relevant memories from Chroma
async function retrieveRelevantMemories(sessionId, query, topK = 3) {
  try {
    if (!memoryCollection) {
      return [];
    }

    // Similarity threshold tuning:
    // Distance 0 = identical, 2 = completely different
    // Testing showed:
    // 0.8: Strict (rejects good memories in some cases, distance 1.323)
    // 0.9: Balanced (passes most tests)
    // 1.0: More lenient (safer for persistence)
    // Using 0.95 as sweet spot between both
    const SIMILARITY_THRESHOLD = 0.95;

    const embedding = await generateEmbedding(query);
    
    const results = await memoryCollection.query({
      queryEmbeddings: [embedding],
      nResults: topK,
      where: { sessionId: sessionId }
    });

    if (!results || !results.documents || results.documents.length === 0) {
      console.log(`[Memory] Session: ${sessionId} - No memories found`);
      return [];
    }

    const memories = results.documents[0] || [];
    const distances = results.distances[0] || [];
    
    // Filter by similarity threshold
    const filteredMemories = memories.filter((memory, index) => {
      const distance = distances[index];
      if (distance > SIMILARITY_THRESHOLD) {
        console.log(`[Memory] Filtering out low-similarity memory (distance: ${distance.toFixed(3)} > ${SIMILARITY_THRESHOLD}): "${memory.substring(0, 50)}..."`);
        return false;
      }
      return true;
    });

    console.log(`[Memory] Session: ${sessionId} - Retrieved: ${filteredMemories.length} memories (filtered from ${memories.length})`);
    return filteredMemories;
  } catch (error) {
    console.error('[Memory] Memory retrieval failed:', error.message);
    return [];
  }
}

// Extract durable memory from user message
async function extractDurableMemory(userMessage) {
  try {
    const extractionPrompt = `Analyze this user message and determine if it contains a durable fact worth remembering (preference, recurring task, personal detail, or explicit instruction to remember something).

User message: "${userMessage}"

If the message contains a durable fact worth remembering, respond with ONLY the fact in a concise form (e.g., "User prefers dark mode", "User works late at night").

If the message is a question, greeting, temporary request, or does NOT contain a memorable fact, respond with exactly: NONE

Examples:
"I prefer dark mode" → "User prefers dark mode"
"I usually work late at night" → "User usually works late at night"
"Remember that I like concise answers" → "User prefers concise answers"
"What's the capital of France?" → NONE
"Hello" → NONE
"Thanks" → NONE

Response:`;

    let extraction;
    
    if (LLM_PROVIDER === 'local') {
      const response = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: OLLAMA_MODEL,
          messages: [{ role: 'user', content: extractionPrompt }],
          stream: false
        })
      });
      
      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      extraction = data.message.content.trim();
    } else {
      const model = genAI.getGenerativeModel({ model: 'gemini-3.6-flash' });
      const result = await model.generateContent(extractionPrompt);
      extraction = result.response.text().trim();
    }
    
    if (extraction === 'NONE' || extraction.toLowerCase().includes('none')) {
      return null;
    }

    console.log(`[Memory] Extracted durable fact: "${extraction}"`);
    return extraction;
  } catch (error) {
    console.error('[Memory] Memory extraction failed:', error.message);
    return null;
  }
}

// Store memory in Chroma
async function storeMemory(sessionId, memoryText) {
  try {
    if (!memoryCollection) {
      console.warn('[Memory] Collection not initialized, skipping storage');
      return;
    }

    const embedding = await generateEmbedding(memoryText);
    const memoryId = `mem_${uuidv4()}`;

    await memoryCollection.add({
      ids: [memoryId],
      embeddings: [embedding],
      documents: [memoryText],
      metadatas: [{
        sessionId: sessionId,
        type: 'user_fact',
        timestamp: Date.now()
      }]
    });

    console.log(`[Memory] Stored memory: ${memoryId} for session ${sessionId}`);
  } catch (error) {
    console.error('[Memory] Memory storage failed:', error.message);
  }
}

// Build context with conversation history and memories
function buildContextPrompt(sessionId, userMessage, relevantMemories) {
  const session = getSession(sessionId);
  let contextPrompt = SYSTEM_PROMPT + '\n\n';

  // Add relevant memories if available
  if (relevantMemories && relevantMemories.length > 0) {
    contextPrompt += 'RELEVANT USER MEMORIES:\n';
    relevantMemories.forEach(mem => {
      contextPrompt += `- ${mem}\n`;
    });
    contextPrompt += '\n';
  }

  // Add recent conversation history
  if (session.turns.length > 0) {
    contextPrompt += 'RECENT CONVERSATION:\n';
    session.turns.forEach(turn => {
      contextPrompt += `User: ${turn.user}\n`;
      contextPrompt += `Assistant: ${turn.assistant}\n\n`;
    });
  }

  // Add current message
  contextPrompt += `CURRENT USER MESSAGE:\n${userMessage}\n\n`;
  contextPrompt += 'Answer the current user message naturally based on the context provided above.';

  return contextPrompt;
}

// Main endpoint: accepts audio, returns audio
app.post('/converse', upload.single('audio'), async (req, res) => {
  try {
    // Validate input
    if (!req.file) {
      return res.status(400).json({ error: 'No audio file provided' });
    }

    // Get or generate session ID
    let sessionId = req.body.sessionId || req.headers['x-session-id'];
    if (!sessionId) {
      sessionId = `session_${uuidv4()}`;
      console.log(`[Memory] Generated new session ID: ${sessionId}`);
    } else {
      console.log(`[Memory] Using session ID: ${sessionId}`);
    }

    console.log(`[1/7] Received audio file: ${req.file.size} bytes`);

    // Step 1: Transcribe audio using Deepgram
    const transcript = await transcribeAudio(req.file.buffer);
    console.log(`[2/7] Transcribed: "${transcript}"`);

    if (!transcript || transcript.trim().length === 0) {
      return res.status(400).json({ error: 'No speech detected in audio' });
    }

    // Step 2: Retrieve relevant memories
    console.log('[3/7] Retrieving relevant memories...');
    const relevantMemories = await retrieveRelevantMemories(sessionId, transcript, 3);

    // Step 3: Build context with conversation history and memories
    const contextPrompt = buildContextPrompt(sessionId, transcript, relevantMemories);

    // Step 4: Get response from LLM with context
    const assistantResponse = await getLLMResponseWithContext(contextPrompt);
    console.log(`[4/7] Assistant response: "${assistantResponse}"`);

    // Step 5: Extract and store durable memory (async, don't block response)
    setImmediate(async () => {
      try {
        console.log('[5/7] Extracting durable memory...');
        const durableMemory = await extractDurableMemory(transcript);
        if (durableMemory) {
          await storeMemory(sessionId, durableMemory);
        }
      } catch (err) {
        console.error('[Memory] Background memory extraction failed:', err.message);
      }
    });

    // Step 6: Add turn to session memory
    addTurnToSession(sessionId, transcript, assistantResponse);

    // Step 7: Convert response to speech using Piper
    console.log('[6/7] Generating speech...');
    const audioBuffer = await textToSpeech(assistantResponse);
    console.log(`[7/7] Generated audio: ${audioBuffer.length} bytes`);

    // Return audio with session ID
    res.set({
      'Content-Type': 'audio/wav',
      'Content-Length': audioBuffer.length,
      'X-Session-ID': sessionId
    });
    res.send(audioBuffer);

  } catch (error) {
    console.error('Error in /converse:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error.message,
      step: error.step || 'unknown'
    });
  }
});

// TEXT-BASED ENDPOINT: For browser avatar frontend
// Accepts JSON text input, returns JSON with text response + base64 audio
app.post('/converse-text', async (req, res) => {
  try {
    const { user_input, sessionId: clientSessionId } = req.body;
    
    if (!user_input || user_input.trim().length === 0) {
      return res.status(400).json({ error: 'No input provided' });
    }

    // Get or generate session ID
    let sessionId = clientSessionId || `session_${uuidv4()}`;
    console.log(`[Avatar] Session: ${sessionId}, Input: "${user_input}"`);

    // Step 1: Retrieve relevant memories
    console.log('[Avatar] Retrieving memories...');
    const relevantMemories = await retrieveRelevantMemories(sessionId, user_input, 3);

    // Step 2: Build context with conversation history and memories
    const contextPrompt = buildContextPrompt(sessionId, user_input, relevantMemories);

    // Step 3: Get response from LLM with context
    const assistantResponse = await getLLMResponseWithContext(contextPrompt);
    console.log(`[Avatar] Response: "${assistantResponse}"`);

    // Step 4: Extract and store durable memory (async, don't block response)
    setImmediate(async () => {
      try {
        console.log('[Avatar] Extracting durable memory...');
        const durableMemory = await extractDurableMemory(user_input);
        if (durableMemory) {
          await storeMemory(sessionId, durableMemory);
        }
      } catch (err) {
        console.error('[Avatar] Memory extraction failed:', err.message);
      }
    });

    // Step 5: Add turn to session memory
    addTurnToSession(sessionId, user_input, assistantResponse);

    // Step 6: Convert response to speech using Piper
    console.log('[Avatar] Generating audio...');
    const audioBuffer = await textToSpeech(assistantResponse);
    const audioBase64 = audioBuffer.toString('base64');
    console.log(`[Avatar] Audio generated: ${audioBuffer.length} bytes`);

    // Return JSON with text response and base64 audio
    res.json({
      sessionId: sessionId,
      user_input: user_input,
      response_text: assistantResponse,
      audio_base64: audioBase64,
      timestamp: Date.now()
    });

  } catch (error) {
    console.error('[Avatar] Error in /converse-text:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
});

// Step 1: Speech-to-Text using Deepgram (unchanged)
async function transcribeAudio(audioBuffer) {
  try {
    const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
      audioBuffer,
      {
        model: 'nova-2',
        smart_format: true,
      }
    );

    if (error) {
      throw new Error(`Deepgram error: ${error.message}`);
    }

    if (!result || !result.results) {
      throw new Error('No transcription result from Deepgram');
    }

    const channels = result.results.channels;
    if (!channels || channels.length === 0) {
      throw new Error('No audio channels in Deepgram response');
    }

    const alternatives = channels[0].alternatives;
    if (!alternatives || alternatives.length === 0) {
      throw new Error('No alternatives in Deepgram response');
    }

    const transcript = alternatives[0].transcript;
    
    if (!transcript || transcript.trim().length === 0) {
      throw new Error('No transcription returned from Deepgram');
    }

    return transcript;
  } catch (error) {
    error.step = 'STT (Deepgram)';
    throw error;
  }
}

// Get response from LLM with context (Gemini in production, Ollama optional in dev)
async function getLLMResponseWithContext(contextPrompt) {
  try {
    // Production: Always use Gemini if provider is explicitly set to 'gemini'
    if (normalizedProvider === 'gemini') {
      return await getGeminiResponse(contextPrompt);
    }
    // Development: Use Ollama
    else if (normalizedProvider === 'local') {
      return await getOllamaResponse(contextPrompt);
    }
    // Fallback: Use Gemini if neither is configured
    else {
      console.warn('[LLM] Unknown provider, falling back to Gemini');
      return await getGeminiResponse(contextPrompt);
    }
  } catch (error) {
    const provider = normalizedProvider === 'local' ? 'Ollama' : 'Gemini';
    error.step = `LLM (${provider})`;
    throw error;
  }
}

// Get response from Ollama local model (with optional function calling support)
async function getOllamaResponse(contextPrompt) {
  try {
    // Simple chat-only mode (for models without tool support)
    if (!TOOLS_ENABLED) {
      const response = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: OLLAMA_MODEL,
          messages: [{ role: 'user', content: contextPrompt }],
          stream: false
        })
      });

      if (!response.ok) {
        // Check if Ollama is unreachable
        if (response.status === 404 || response.status === 503) {
          throw new Error('Local model unavailable — is Ollama running? (try: ollama serve)');
        }
        throw new Error(`Ollama API error: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data || !data.message || !data.message.content) {
        throw new Error('No response from Ollama');
      }

      return data.message.content;
    }

    // Advanced mode: Function calling support (for tool-capable models)
    let messages = [{ role: 'user', content: contextPrompt }];
    let maxIterations = 5; // Prevent infinite loops
    let iteration = 0;

    while (iteration < maxIterations) {
      iteration++;
      
      const response = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: OLLAMA_MODEL,
          messages: messages,
          tools: TOOLS,
          stream: false
        })
      });

      if (!response.ok) {
        // Check if Ollama is unreachable
        if (response.status === 404 || response.status === 503) {
          throw new Error('Local model unavailable — is Ollama running? (try: ollama serve)');
        }
        throw new Error(`Ollama API error: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data || !data.message) {
        throw new Error('No response from Ollama');
      }

      // Add assistant message to conversation
      messages.push(data.message);

      // Check if the model wants to call a tool
      if (data.message.tool_calls && data.message.tool_calls.length > 0) {
        console.log(`[Tools] Model requested ${data.message.tool_calls.length} tool call(s)`);
        
        // Execute each tool call
        for (const toolCall of data.message.tool_calls) {
          const toolName = toolCall.function.name;
          const toolArgs = toolCall.function.arguments;
          
          console.log(`[Tools] Calling: ${toolName}`);
          
          // Execute the tool
          const toolResult = await executeTool(toolName, toolArgs);
          
          // Add tool result to messages
          messages.push({
            role: 'tool',
            content: JSON.stringify(toolResult)
          });
          
          console.log(`[Tools] Result: ${toolResult.success ? 'success' : 'failed'}`);
        }
        
        // Continue the loop to get final response
        continue;
      }

      // No tool calls, return the content
      if (data.message.content) {
        return data.message.content;
      }

      // If no content and no tool calls, something went wrong
      throw new Error('No content in Ollama response');
    }

    throw new Error('Max tool calling iterations reached');
  } catch (error) {
    console.error('[LLM] Ollama error:', error.message);
    
    // Enhanced error message for common failures
    if (error.code === 'ECONNREFUSED' || error.message.includes('fetch failed')) {
      throw new Error('Local model unavailable — is Ollama running? (try: ollama serve)');
    }
    
    throw error;
  }
}

// Get response from Gemini (cloud)
async function getGeminiResponse(contextPrompt) {
  try {
    const model = genAI.getGenerativeModel({ 
      model: 'gemini-3.6-flash',
    });

    const result = await model.generateContent(contextPrompt);
    const response = result.response.text();
    
    if (!response) {
      throw new Error('No response from Gemini');
    }

    return response;
  } catch (error) {
    console.error('[LLM] Gemini error:', error.message);
    throw error;
  }
}

// Step 3: Text-to-Speech using Piper (unchanged)
async function textToSpeech(text) {
  const tempFile = path.join(__dirname, `temp-tts-${Date.now()}-${Math.random().toString(36).substring(7)}.wav`);
  
  try {
    const piperPath = path.join(__dirname, 'piper-venv', 'bin', 'python');
    const modelPath = path.join(__dirname, 'piper-voices', 'en_US-lessac-medium.onnx');
    
    // Run Piper TTS using the installed Python environment
    await new Promise((resolve, reject) => {
      const piperProcess = spawn(piperPath, [
        '-m', 'piper',
        '--model', modelPath,
        '--output_file', tempFile
      ]);
      
      let stderr = '';
      
      // Send text to Piper via stdin
      piperProcess.stdin.write(text);
      piperProcess.stdin.end();
      
      piperProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      piperProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Piper process exited with code ${code}: ${stderr}`));
        } else {
          resolve();
        }
      });
      
      piperProcess.on('error', (err) => {
        reject(new Error(`Failed to start Piper process: ${err.message}`));
      });
    });
    
    // Read the generated WAV file
    const audioBuffer = fs.readFileSync(tempFile);
    
    // Clean up temporary file
    try {
      fs.unlinkSync(tempFile);
    } catch (cleanupErr) {
      console.warn(`Warning: Could not delete temp file ${tempFile}:`, cleanupErr.message);
    }
    
    return audioBuffer;
  } catch (error) {
    // Clean up temp file on error
    try {
      if (fs.existsSync(tempFile)) {
        fs.unlinkSync(tempFile);
      }
    } catch (cleanupErr) {
      // Ignore cleanup errors
    }
    
    error.step = 'TTS (Piper)';
    throw error;
  }
}

// Serve static files - BEFORE API routes so they don't intercept
app.use(express.static('.', { 
  setHeaders: (res, path) => {
    if (path.endsWith('.glb')) {
      res.setHeader('Content-Type', 'model/gltf-binary');
      res.setHeader('Access-Control-Allow-Origin', '*');
    } else if (path.endsWith('.html')) {
      res.setHeader('Content-Type', 'text/html');
    }
  }
}));

// Serve avatar page as landing (main page)
app.get('/', (req, res) => {
  res.status(404).json({ error: 'Not found', message: 'Use /health to check service status or /converse to send audio' });
});

// Serve old test page
app.get('/test', (req, res) => {
  res.status(404).json({ error: 'Not found', message: 'Test page has been removed. Use API endpoints instead.' });
});

// Health check endpoint
app.get('/health', async (req, res) => {
  const health = {
    status: 'ok',
    services: {
      deepgram: !!process.env.DEEPGRAM_API_KEY,
      gemini: !!process.env.GEMINI_API_KEY,
      piper: fs.existsSync(path.join(__dirname, 'piper-venv', 'bin', 'python')),
      chroma: memoryCollection !== null,
      ollama: {
        reachable: false,
        model_available: false,
        model_name: OLLAMA_MODEL,
        tools_enabled: TOOLS_ENABLED,
        note: normalizedProvider === 'gemini' ? 'Production mode: Ollama not used' : 'Development mode: Ollama enabled'
      }
    }
  };

  // Check Ollama connectivity only if in development mode
  if (normalizedProvider === 'local') {
    try {
      // Check if Ollama is reachable
      const tagsResponse = await fetch(`${OLLAMA_BASE_URL}/api/tags`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000) // 3 second timeout
      });

      if (tagsResponse.ok) {
        health.services.ollama.reachable = true;
        
        // Check if the specific model is available
        const data = await tagsResponse.json();
        const models = data.models || [];
        const modelExists = models.some(m => m.name === OLLAMA_MODEL || m.name === `${OLLAMA_MODEL}:latest`);
        
        health.services.ollama.model_available = modelExists;
        health.services.ollama.available_models = models.map(m => m.name);
        
        if (!modelExists) {
          health.services.ollama.error = `Model "${OLLAMA_MODEL}" not found. Available: ${models.map(m => m.name).join(', ') || 'none'}`;
        }
      } else {
        health.services.ollama.error = `Ollama responded with status ${tagsResponse.status}`;
      }
    } catch (error) {
      health.services.ollama.error = error.message.includes('aborted') 
        ? 'Ollama not responding (timeout)' 
        : `Cannot reach Ollama: ${error.message}`;
    }
  }

  // Overall health status
  let criticalServicesOk = health.services.deepgram && 
                           health.services.piper && 
                           health.services.chroma;
  
  // Check LLM based on provider
  if (normalizedProvider === 'gemini') {
    criticalServicesOk = criticalServicesOk && health.services.gemini;
  } else if (normalizedProvider === 'local') {
    criticalServicesOk = criticalServicesOk && health.services.ollama.reachable && health.services.ollama.model_available;
  }
  
  health.status = criticalServicesOk ? 'healthy' : 'degraded';

  res.json(health);
});

// Start server
const PORT = process.env.PORT || 3000;

// Initialize Chroma before starting server
initializeChroma().then(() => {
  app.listen(PORT, () => {
    console.log(`🎤 Voice Assistant Backend running on port ${PORT}`);
    console.log(`\n📍 Endpoints:`);
    console.log(`   GET  /             - Test page (open in browser)`);
    console.log(`   GET  /avatar.html  - 3D Avatar with voice (browser UI)`);
    console.log(`   POST /converse     - Voice API (send audio, receive audio)`);
    console.log(`   POST /converse-text - Text API (send text, receive text + audio)`);
    console.log(`   GET  /health       - Service status`);
    console.log(`   GET  /health    - Service status`);
    console.log(`\n💾 Phase 2 Features:`);
    console.log(`   - Session-based conversation memory (10 turns)`);
    console.log(`   - Persistent vector store (Chroma)`);
    console.log(`   - Durable memory extraction`);
    
    // Check for missing API keys
    const missing = [];
    if (!process.env.DEEPGRAM_API_KEY) missing.push('DEEPGRAM_API_KEY');
    if (!process.env.GEMINI_API_KEY) missing.push('GEMINI_API_KEY');
    
    if (missing.length > 0) {
      console.warn(`⚠️  Warning: Missing API keys: ${missing.join(', ')}`);
      console.warn(`   Copy .env.example to .env and add your keys`);
    }
  });
}).catch(error => {
  console.error('Failed to initialize server:', error);
  process.exit(1);
});
