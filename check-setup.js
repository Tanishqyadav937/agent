#!/usr/bin/env node

/**
 * Setup validation script
 * Checks if all required API keys are configured
 * 
 * Usage: node check-setup.js
 */

import dotenv from 'dotenv';
import fs from 'fs';

console.log('🔍 Voice Assistant Setup Checker\n');

// Check if .env file exists
if (!fs.existsSync('.env')) {
  console.log('❌ .env file not found');
  console.log('   Run: cp .env.example .env');
  console.log('   Then edit .env and add your API keys\n');
  process.exit(1);
}

console.log('✅ .env file exists\n');

// Load environment variables
dotenv.config();

// Check each required API key
const checks = [
  {
    name: 'Deepgram API Key',
    env: 'DEEPGRAM_API_KEY',
    url: 'https://deepgram.com/',
    required: true
  },
  {
    name: 'Google Gemini API Key',
    env: 'GEMINI_API_KEY',
    url: 'https://ai.google.dev/',
    required: true
  },
  {
    name: 'ElevenLabs API Key',
    env: 'ELEVENLABS_API_KEY',
    url: 'https://elevenlabs.io/',
    required: true
  },
  {
    name: 'ElevenLabs Voice ID',
    env: 'ELEVENLABS_VOICE_ID',
    url: 'https://elevenlabs.io/voice-library',
    required: false,
    default: '21m00Tcm4TlvDq8ikWAM (Rachel)'
  },
  {
    name: 'Server Port',
    env: 'PORT',
    required: false,
    default: '3000'
  }
];

let hasErrors = false;

checks.forEach(check => {
  const value = process.env[check.env];
  const hasValue = value && value.trim().length > 0;

  if (check.required) {
    if (hasValue) {
      console.log(`✅ ${check.name}`);
      console.log(`   ${value.substring(0, 20)}...`);
    } else {
      console.log(`❌ ${check.name} - MISSING`);
      console.log(`   Get one at: ${check.url}`);
      console.log(`   Set ${check.env} in .env file`);
      hasErrors = true;
    }
  } else {
    if (hasValue) {
      console.log(`✅ ${check.name}: ${value}`);
    } else {
      console.log(`ℹ️  ${check.name}: Using default (${check.default})`);
    }
  }
  console.log();
});

// Summary
console.log('─'.repeat(50));
if (hasErrors) {
  console.log('\n❌ Setup incomplete - missing required API keys');
  console.log('\nNext steps:');
  console.log('1. Sign up for the services listed above');
  console.log('2. Get your API keys from their dashboards');
  console.log('3. Add them to your .env file');
  console.log('4. Run this script again to verify\n');
  process.exit(1);
} else {
  console.log('\n✅ All required API keys configured!');
  console.log('\nYou can now start the server:');
  console.log('   npm start');
  console.log('\nOr test it:');
  console.log('   open http://localhost:3000\n');
  process.exit(0);
}
