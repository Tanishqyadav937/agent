# Quick Start Guide

## 1. Get API Keys

You need three API keys:

### Deepgram (Speech-to-Text)
1. Go to https://deepgram.com/
2. Sign up for a free account
3. Navigate to API Keys in dashboard
4. Create a new API key

### Google Gemini (LLM)
1. Go to https://ai.google.dev/
2. Sign up / Sign in with Google account
3. Navigate to "Get API key" in Google AI Studio
4. Create a new API key

### ElevenLabs (Text-to-Speech)
1. Go to https://elevenlabs.io/
2. Sign up for a free account
3. Go to Profile → API Keys
4. Generate a new API key

## 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor

# Verify your setup
npm run check
```

Your `.env` should look like:
```
DEEPGRAM_API_KEY=abc123...
GEMINI_API_KEY=AIza...
ELEVENLABS_API_KEY=xyz789...
PORT=3000
```

## 3. Start the Server

```bash
npm start
```

You should see:
```
🎤 Voice Assistant Backend running on port 3000
POST /converse - Send audio file, receive audio response
GET  /health   - Check service status
```

## 4. Test the API

### Option A: Using curl

Record a short audio message (or use any WAV/MP3 file), then:

```bash
./test-curl.sh your-recording.wav
```

Or manually:
```bash
curl -X POST http://localhost:3000/converse \
  -F "audio=@recording.wav" \
  --output response.mp3

# Play the response (macOS)
afplay response.mp3
```

### Option B: Using Node.js test client

```bash
node test-client.js your-recording.wav
```

### Option C: Check health status

```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "ok",
  "services": {
    "deepgram": true,
    "gemini": true,
    "elevenlabs": true
  }
}
```

## 5. Recording Audio for Testing

### macOS (using QuickTime)
1. Open QuickTime Player
2. File → New Audio Recording
3. Click record, speak, click stop
4. Save as `test.wav`

### Using SoX (command line)
```bash
# Install sox
brew install sox

# Record 5 seconds
sox -d -r 16000 -c 1 recording.wav trim 0 5
```

### Using ffmpeg
```bash
# Record from microphone
ffmpeg -f avfoundation -i ":0" -t 5 recording.wav
```

## Example Test Flow

```bash
# 1. Start server
npm start

# 2. In another terminal, check health
curl http://localhost:3000/health

# 3. Record audio (say "Hello, what's the weather like?")
sox -d -r 16000 -c 1 test.wav trim 0 5

# 4. Test the assistant
./test-curl.sh test.wav

# 5. Play response
afplay response.mp3
```

## Troubleshooting

### Missing API keys
If you see warnings about missing keys, make sure your `.env` file is in the project root and contains all three API keys.

### "No audio file provided"
Make sure you're sending the file as form-data with the field name `audio`:
```bash
curl -F "audio=@file.wav" http://localhost:3000/converse
```

### "No speech detected in audio"
- Check your audio file is not empty
- Try speaking louder or closer to the microphone
- Verify the audio format is supported (WAV, MP3, FLAC, etc.)

### API errors (500)
Check the server logs - it will indicate which step failed:
- `STT (Deepgram)` - Check Deepgram API key and audio format
- `LLM (Gemini)` - Check Gemini API key and quota
- `TTS (ElevenLabs)` - Check ElevenLabs API key and quota

## What Happens Behind the Scenes

When you POST audio to `/converse`:

1. **Audio Upload** → Server receives your audio file
2. **Deepgram STT** → Audio is transcribed to text
3. **Gemini LLM** → Transcript is sent to Gemini with system prompt
4. **ElevenLabs TTS** → Gemini's response is converted to speech
5. **Audio Response** → MP3 audio is returned

Each step includes error handling, and failures will tell you which step broke.
