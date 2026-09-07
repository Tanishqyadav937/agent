#!/usr/bin/env node

/**
 * Test client for the voice assistant API
 * 
 * Usage:
 *   node test-client.js <audio-file-path>
 * 
 * Example:
 *   node test-client.js recording.wav
 */

import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const API_URL = process.env.API_URL || 'http://localhost:3000/converse';

async function testVoiceAssistant(audioFilePath) {
  try {
    console.log(`🎤 Testing voice assistant with: ${audioFilePath}`);
    console.log(`📡 API endpoint: ${API_URL}\n`);

    // Check if file exists
    if (!fs.existsSync(audioFilePath)) {
      console.error(`❌ Error: File not found: ${audioFilePath}`);
      process.exit(1);
    }

    // Read audio file
    const audioBuffer = fs.readFileSync(audioFilePath);
    console.log(`📁 Audio file size: ${audioBuffer.length} bytes`);

    // Create form data
    const formData = new FormData();
    const audioBlob = new Blob([audioBuffer], { type: 'audio/wav' });
    formData.append('audio', audioBlob, 'recording.wav');

    // Send request
    console.log(`⏳ Sending request...`);
    const startTime = Date.now();

    const response = await fetch(API_URL, {
      method: 'POST',
      body: formData,
    });

    const duration = Date.now() - startTime;

    if (!response.ok) {
      const error = await response.json();
      console.error(`❌ Error ${response.status}:`, error);
      process.exit(1);
    }

    // Save response audio
    const audioArrayBuffer = await response.arrayBuffer();
    const responseBuffer = Buffer.from(audioArrayBuffer);
    
    const outputPath = 'response.mp3';
    fs.writeFileSync(outputPath, responseBuffer);

    console.log(`\n✅ Success! (${duration}ms)`);
    console.log(`🔊 Response saved to: ${outputPath}`);
    console.log(`📊 Response size: ${responseBuffer.length} bytes`);
    console.log(`\nPlay with: afplay ${outputPath}`);

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

// Main
const audioFile = process.argv[2];
if (!audioFile) {
  console.log('Usage: node test-client.js <audio-file-path>');
  console.log('Example: node test-client.js recording.wav');
  process.exit(1);
}

testVoiceAssistant(audioFile);
