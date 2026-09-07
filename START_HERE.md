# 🎤 Voice Assistant Backend

## Welcome! Start Here 👋

This is a **minimal voice assistant backend** that connects:
- 🎤 **Deepgram** (speech-to-text)
- 🧠 **Google Gemini** (conversational AI)  
- 🔊 **ElevenLabs** (text-to-speech)

**One endpoint:** Send audio → Get audio response!

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Install
npm install

# 2. Setup API keys
cp .env.example .env
# Edit .env and add your 3 API keys

# 3. Verify setup
npm run check

# 4. Start server
npm start

# 5. Test in browser
open http://localhost:3000
```

**Click → Speak → Listen!** That's it! 🎉

---

## 📚 Documentation Guide

Choose your path:

### 🆕 First Time Here?

Read in this order:

1. **[CHECKLIST.md](CHECKLIST.md)** ← Step-by-step setup checklist
2. **[QUICKSTART.md](QUICKSTART.md)** ← Get running in 5 minutes  
3. **[OVERVIEW.md](OVERVIEW.md)** ← Visual guide to what you built
4. **Test in browser** → http://localhost:3000
5. All done! 🎊

### 🏃 Want to Start Quickly?

**Fast track:**
```bash
npm install
cp .env.example .env
# Add your API keys to .env
npm start
open http://localhost:3000
```

**API keys needed:**
- Deepgram: https://deepgram.com/
- Google Gemini: https://ai.google.dev/
- ElevenLabs: https://elevenlabs.io/

All have free tiers!

### 🔬 Want to Understand the Code?

Read these:

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep-dive
2. **[server.js](server.js)** - The actual code (189 lines)
3. **[TESTING.md](TESTING.md)** - How to test everything

### 🧪 Want to Test?

Three testing methods:

1. **Browser** → `npm start` then open http://localhost:3000
2. **Command Line** → `./test-curl.sh recording.wav`
3. **Node.js** → `node test-client.js recording.wav`

See **[TESTING.md](TESTING.md)** for details.

### 🤔 Something Not Working?

1. Run `npm run check` to verify setup
2. Check **[TESTING.md](TESTING.md)** troubleshooting section
3. Review error messages in server console

### 📖 Want Full Details?

Complete documentation:

- **[README.md](README.md)** - Project overview & API docs
- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup guide
- **[OVERVIEW.md](OVERVIEW.md)** - Visual guide with diagrams
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical details
- **[TESTING.md](TESTING.md)** - Testing & troubleshooting
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - What was built & why
- **[CHECKLIST.md](CHECKLIST.md)** - Step-by-step checklist

---

## 🎯 What Does This Do?

```
You speak → AI transcribes → AI thinks → AI responds → You hear
   (🎤)    →    (📝)      →   (🧠)   →    (🔊)    →  (👂)
```

**Example:**

```
You: "Hello, what's 2 plus 2?"
AI: "Hello! 2 plus 2 equals 4. Is there anything else I can help you with?"
```

All in ~8 seconds!

---

## 📁 Project Structure

```
voice-assistant-backend/
│
├── 🚀 Core
│   ├── server.js              ← The main application
│   ├── package.json           ← Dependencies
│   └── .env                   ← Your API keys (create this!)
│
├── 📖 Documentation (7 guides)
│   ├── START_HERE.md          ← You are here!
│   ├── CHECKLIST.md           ← Step-by-step setup
│   ├── QUICKSTART.md          ← 5-minute guide
│   ├── OVERVIEW.md            ← Visual guide
│   ├── README.md              ← Full documentation
│   ├── ARCHITECTURE.md        ← Technical details
│   ├── TESTING.md             ← Testing guide
│   └── PROJECT_SUMMARY.md     ← Big picture
│
├── 🧪 Testing
│   ├── test.html              ← Browser test UI
│   ├── test-curl.sh           ← Curl test script
│   └── test-client.js         ← Node.js client
│
└── 🛠️ Utilities
    ├── check-setup.js         ← Validate API keys
    └── .env.example           ← Environment template
```

---

## ⚡ Command Reference

```bash
# Installation
npm install                    # Install dependencies

# Configuration
cp .env.example .env          # Create config file
npm run check                 # Verify API keys

# Running
npm start                     # Start server
npm run dev                   # Start with auto-reload

# Testing
open http://localhost:3000    # Browser test
./test-curl.sh test.wav       # Command line test
node test-client.js test.wav  # Node.js test
curl http://localhost:3000/health  # Health check
```

---

## 🎓 Learning Paths

### Path 1: Just Make It Work (Fastest)
```
1. CHECKLIST.md
2. Set up API keys
3. npm start
4. Test in browser
✓ Done!
```

### Path 2: Understand What You Built
```
1. OVERVIEW.md (visual guide)
2. QUICKSTART.md (setup)
3. Test in browser
4. ARCHITECTURE.md (how it works)
5. Experiment and customize!
```

### Path 3: Full Deep Dive
```
1. All documentation in order
2. Read server.js code
3. Try all testing methods
4. Extend with new features
5. Build something awesome!
```

---

## ✨ Features

✅ Complete STT → LLM → TTS pipeline  
✅ Single API endpoint (`POST /converse`)  
✅ Multi-format audio support  
✅ Error handling with step tracking  
✅ Browser test interface  
✅ Command line testing tools  
✅ Comprehensive documentation  
✅ Production-ready code structure  

---

## 🔑 Requirements

**You need:**
- Node.js 26+ 
- Three free API keys:
  - Deepgram (https://deepgram.com/)
  - Google Gemini (https://ai.google.dev/)
  - ElevenLabs (https://elevenlabs.io/)

**Time to setup:** ~10 minutes  
**Cost:** Free tier available for all services!

---

## 💡 What Can You Build?

This is your foundation for:

- Smart home assistants
- Mobile app voice features
- Phone/IVR systems
- Voice-controlled apps
- Educational tools
- Accessibility features
- Customer service bots
- And much more!

---

## 🎯 Next Steps

### Just Starting?
→ Go to **[CHECKLIST.md](CHECKLIST.md)**

### Ready to Code?
→ Read **[ARCHITECTURE.md](ARCHITECTURE.md)**

### Want to Test?
→ Follow **[TESTING.md](TESTING.md)**

### Need Quick Setup?
→ Read **[QUICKSTART.md](QUICKSTART.md)**

### Want the Big Picture?
→ Check **[OVERVIEW.md](OVERVIEW.md)**

---

## 🆘 Need Help?

**Setup issues?**
1. Run `npm run check`
2. See [CHECKLIST.md](CHECKLIST.md)

**Testing issues?**
1. Check [TESTING.md](TESTING.md) troubleshooting
2. Review server console logs

**Understanding the code?**
1. Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Check inline comments in `server.js`

---

## 🎉 Ready to Begin?

**Three options:**

1. **Guided Setup** → [CHECKLIST.md](CHECKLIST.md)
2. **Quick Start** → [QUICKSTART.md](QUICKSTART.md)  
3. **Visual Guide** → [OVERVIEW.md](OVERVIEW.md)

**Or just dive in:**
```bash
npm install && npm start
```

---

**Welcome to your voice AI assistant! Let's build something amazing! 🚀**
