# Getting Started Checklist

Follow these steps to get your voice assistant running:

## ☐ Prerequisites

- [ ] Node.js 26+ installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Text editor (VS Code, vim, nano, etc.)
- [ ] Terminal/command line access

## ☐ Installation

- [ ] Navigate to project directory
- [ ] Run `npm install`
- [ ] Verify no installation errors

## ☐ Get API Keys

### Deepgram (Speech-to-Text)
- [ ] Visit https://deepgram.com/
- [ ] Sign up for free account
- [ ] Go to dashboard → API Keys
- [ ] Create new API key
- [ ] Copy the key

### Google Gemini (LLM)
- [ ] Visit https://ai.google.dev/
- [ ] Sign up / Sign in with Google account
- [ ] Go to Google AI Studio
- [ ] Navigate to "Get API key"
- [ ] Create new API key
- [ ] Copy the key

### ElevenLabs (Text-to-Speech)
- [ ] Visit https://elevenlabs.io/
- [ ] Sign up for free account
- [ ] Go to Profile → API Keys
- [ ] Generate new API key
- [ ] Copy the key

## ☐ Configuration

- [ ] Copy `.env.example` to `.env`
  ```bash
  cp .env.example .env
  ```
- [ ] Open `.env` in your text editor
- [ ] Paste Deepgram API key after `DEEPGRAM_API_KEY=`
- [ ] Paste Gemini API key after `GEMINI_API_KEY=`
- [ ] Paste ElevenLabs API key after `ELEVENLABS_API_KEY=`
- [ ] Save the file
- [ ] Run `npm run check` to verify

## ☐ First Test

- [ ] Start the server: `npm start`
- [ ] Verify you see "Voice Assistant Backend running"
- [ ] Check no error messages about missing keys
- [ ] Open browser to http://localhost:3000
- [ ] Click "Start Recording"
- [ ] Grant microphone permissions
- [ ] Say something (e.g., "Hello, how are you?")
- [ ] Click "Stop Recording"
- [ ] Wait for processing (~8 seconds)
- [ ] Hear the AI response!

## ☐ Troubleshooting (If Needed)

### Server won't start
- [ ] Check all API keys are in `.env`
- [ ] Run `npm run check` to validate
- [ ] Check port 3000 isn't already in use

### Microphone not working
- [ ] Grant browser microphone permissions
- [ ] Try Chrome or Firefox (better support)
- [ ] Check system microphone is working

### "No speech detected"
- [ ] Speak louder and clearer
- [ ] Check microphone isn't muted
- [ ] Try command line test with a pre-recorded file

### API Errors
- [ ] Verify API keys are correct (no extra spaces)
- [ ] Check you have API credits/quota
- [ ] Check network connection

### Still not working?
- [ ] Read `TESTING.md` for detailed troubleshooting
- [ ] Check server console logs for specific errors
- [ ] Try the curl test: `./test-curl.sh recording.wav`

## ☐ Next Steps (Optional)

- [ ] Try command line testing (`./test-curl.sh`)
- [ ] Test with different voices (change `ELEVENLABS_VOICE_ID`)
- [ ] Customize system prompt in `server.js`
- [ ] Read `ARCHITECTURE.md` to understand the code
- [ ] Explore extending with memory/tools

## ✅ Success Criteria

You know it's working when:

✓ Server starts without errors  
✓ Browser test page loads  
✓ Can record your voice  
✓ Transcript is generated  
✓ AI responds with text  
✓ Audio response plays  
✓ Total process takes ~8 seconds  

---

## Quick Reference

**Start server:**
```bash
npm start
```

**Check setup:**
```bash
npm run check
```

**Test in browser:**
```bash
open http://localhost:3000
```

**Test with file:**
```bash
./test-curl.sh recording.wav
```

**Check health:**
```bash
curl http://localhost:3000/health
```

---

## Time Estimate

- **API key setup:** 5-10 minutes (first time)
- **Installation:** 1-2 minutes
- **Configuration:** 1-2 minutes
- **First test:** 1 minute

**Total:** ~10-15 minutes from zero to working!

---

**Once everything is checked off, you're done!** 🎉

Your voice assistant is ready to use.
