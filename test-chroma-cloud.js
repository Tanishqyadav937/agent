#!/usr/bin/env node

/**
 * Quick test script to verify Chroma Cloud connection
 * Run: node test-chroma-cloud.js
 */

import { CloudClient } from 'chromadb';
import dotenv from 'dotenv';

dotenv.config();

const CHROMA_API_KEY = process.env.CHROMA_API_KEY;
const CHROMA_TENANT = process.env.CHROMA_TENANT;
const CHROMA_DATABASE = process.env.CHROMA_DATABASE;

console.log('🧪 Testing Chroma Cloud Connection...\n');
console.log('Configuration:');
console.log(`  API Key: ${CHROMA_API_KEY ? '✓ Set' : '✗ Missing'}`);
console.log(`  Tenant: ${CHROMA_TENANT ? `✓ ${CHROMA_TENANT}` : '✗ Missing'}`);
console.log(`  Database: ${CHROMA_DATABASE ? `✓ ${CHROMA_DATABASE}` : '✗ Missing'}`);
console.log('');

if (!CHROMA_API_KEY || !CHROMA_TENANT || !CHROMA_DATABASE) {
  console.error('❌ Error: Missing required Chroma Cloud credentials in .env');
  console.error('');
  console.error('Required environment variables:');
  console.error('  - CHROMA_API_KEY');
  console.error('  - CHROMA_TENANT');
  console.error('  - CHROMA_DATABASE');
  console.error('');
  console.error('Get these from: https://console.trychroma.com/');
  process.exit(1);
}

async function testConnection() {
  try {
    console.log('Connecting to Chroma Cloud...');
    const client = new CloudClient({
      apiKey: CHROMA_API_KEY,
      tenant: CHROMA_TENANT,
      database: CHROMA_DATABASE
    });

    console.log('✓ CloudClient instantiated\n');

    console.log('Getting or creating collection "test_connection"...');
    const collection = await client.getOrCreateCollection({
      name: 'test_connection',
      metadata: { description: 'Connection test collection' }
    });

    console.log('✓ Collection retrieved/created\n');
    console.log(`  Collection name: ${collection.name}`);
    console.log(`  Collection metadata:`, collection.metadata);

    // Try adding a test document
    console.log('\nAdding test document...');
    await collection.add({
      ids: ['test_doc_1'],
      documents: ['This is a test document to verify Chroma Cloud connection'],
      metadatas: [{ test: true, timestamp: new Date().toISOString() }]
    });

    console.log('✓ Document added successfully\n');

    // Try retrieving it
    console.log('Retrieving test document...');
    const results = await collection.get({
      ids: ['test_doc_1']
    });

    console.log('✓ Document retrieved\n');
    console.log('Retrieved document:');
    console.log(`  ID: ${results.ids[0]}`);
    console.log(`  Document: ${results.documents[0]}`);
    console.log(`  Metadata:`, results.metadatas[0]);

    // Clean up
    console.log('\nCleaning up test document...');
    await collection.delete({
      ids: ['test_doc_1']
    });

    console.log('✓ Test document deleted\n');

    console.log('✅ All Chroma Cloud tests passed!\n');
    console.log('Your Chroma Cloud connection is working correctly.');
    console.log('You can now safely deploy to Render with these credentials.');

  } catch (error) {
    console.error('\n❌ Error during Chroma Cloud connection test:');
    console.error(`  ${error.message}`);
    console.error('\nFull error details:');
    console.error(error);
    console.error('\nTroubleshooting tips:');
    console.error('  1. Verify credentials are correct in .env');
    console.error('  2. Check that Chroma Cloud account is active');
    console.error('  3. Ensure API key has proper permissions');
    console.error('  4. Check network connectivity');
    process.exit(1);
  }
}

testConnection();
