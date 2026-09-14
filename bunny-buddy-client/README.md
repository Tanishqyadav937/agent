# Bunny Buddy — Client

A voice front end for the Bunny Buddy backend (Express + Deepgram + Gemini/Ollama + Piper),
built around the [assistant-ui Orb](https://www.assistant-ui.com/elements/orb) — used here in
its **standalone, props-driven form** (no assistant-ui runtime / chat provider needed), since
Bunny Buddy's backend is a plain REST API rather than an assistant-ui-compatible transport.

## What's here

```
src/
  components/
    voice-orb.tsx      the WebGL orb itself, copied verbatim from assistant-ui's
                        elements/voice.tsx (only the `cn` import path was changed)
    voice-control.tsx   connect / mute / disconnect bar + status dot, built to match
                        the Orb's anatomy since the standalone package doesn't ship
                        VoiceControl (that only exists in the runtime-connected version)
  hooks/
    use-bunny-voice-session.ts
                        mic capture, push-to-talk recording (MediaRecorder), live
                        volume metering (Web Audio AnalyserNode) for both your mic
                        and the returned audio, and the round trip to the backend
  lib/
    bunny-api.ts        fetch wrappers for POST /converse, POST /converse-text, GET /health
  App.tsx               wires it all together into one screen
```

## How the orb states map onto Bunny Buddy

`VoiceOrb` only knows five states: `idle | connecting | listening | speaking | muted`.
Bunny Buddy's backend is request/response (no live WebRTC session), so the mapping is:

| Orb state    | When                                                              |
| ------------ | ------------------------------------------------------------------ |
| `idle`       | Not connected — mic permission not yet granted                    |
| `connecting` | Requesting mic permission, **and** while a `/converse` request is in flight (STT → memory → LLM → TTS) |
| `listening`  | Connected, mic armed; live volume while you're recording an utterance |
| `speaking`   | Playing back the WAV Bunny Buddy returned; volume comes from the playback audio itself |
| `muted`      | You've muted the mic                                              |

Interaction is **tap-to-talk**: tap the orb to start recording, tap again to send. A
press-and-hold model doesn't fit well here since a full turn (STT + memory + LLM + TTS)
takes several seconds per the architecture doc's own performance table.

## Wiring it to your backend

1. Copy this whole `bunny-buddy-client/` folder next to your `server.js` project (or
   wherever you're keeping the frontend, per the architecture doc's `project-root/`).
2. Set the backend URL in `.env`:
   ```
   VITE_BUNNY_API_URL=http://localhost:3000
   ```
3. **Enable CORS on the Express backend** for this client's origin (e.g. `http://localhost:5173`
   in dev). The architecture doc already lists `cors` as a dependency — just make sure the
   middleware allows this origin and, if you send `X-Session-ID`, exposes it:
   ```js
   app.use(cors({
     origin: "http://localhost:5173", // or your deployed client origin
     exposedHeaders: ["X-Session-ID"],
   }));
   ```
4. Confirm `/converse` accepts a multipart field named `audio` and returns `audio/wav`
   with an `X-Session-ID` response header — that's what `bunny-api.ts` assumes, matching
   the architecture doc's step 10 (`RETURN AUDIO ... Include X-Session-ID`). If your route
   uses different field/header names, adjust `src/lib/bunny-api.ts` accordingly.

## Run it

```bash
npm install
npm run dev
```

Open the printed local URL, click **Connect** (grants mic access), then tap the orb to talk.

## Notes

- `MediaRecorder` records `audio/webm;codecs=opus`. If Deepgram needs a different container,
  either transcode server-side (ffmpeg) or swap the `mimeType` in `use-bunny-voice-session.ts` —
  Deepgram's prerecorded API does accept webm/opus directly, so this should work as-is.
- No browser storage is used; session state lives in memory only, matching the backend's
  own in-memory session buffer.
