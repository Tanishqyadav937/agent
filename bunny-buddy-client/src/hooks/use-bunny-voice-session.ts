import { useCallback, useEffect, useRef, useState } from "react";
import { converseWithAudio } from "../lib/bunny-api";
import type { VoiceSessionStatus } from "../components/voice-control";

export type TurnRole = "user" | "assistant";
export type VoiceTurn = { id: string; role: TurnRole; label: string };

type Mode = "listening" | "speaking";

/** Live 0..1 volume from an analyser, sampled on a rAF loop. */
function useLevelMeter() {
  const [level, setLevel] = useState(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const dataRef = useRef<Uint8Array<ArrayBuffer> | null>(null);

  const attach = useCallback((analyser: AnalyserNode | null) => {
    analyserRef.current = analyser;
    dataRef.current = analyser
      ? new Uint8Array(new ArrayBuffer(analyser.frequencyBinCount))
      : null;
  }, []);

  useEffect(() => {
    const tick = () => {
      const analyser = analyserRef.current;
      const data = dataRef.current;
      if (analyser && data) {
        analyser.getByteTimeDomainData(data);
        let sumSquares = 0;
        for (let i = 0; i < data.length; i++) {
          const centered = (data[i]! - 128) / 128;
          sumSquares += centered * centered;
        }
        const rms = Math.sqrt(sumSquares / data.length);
        // A little gain so ordinary speech reads clearly on the orb.
        setLevel((prev) => prev * 0.6 + Math.min(1, rms * 3.5) * 0.4);
      } else {
        setLevel((prev) => (prev > 0.01 ? prev * 0.7 : 0));
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return { level, attach };
}

export function useBunnyVoiceSession() {
  const [status, setStatus] = useState<VoiceSessionStatus>("idle");
  const [isMuted, setIsMuted] = useState(false);
  const [mode, setMode] = useState<Mode>("listening");
  const [isRecording, setIsRecording] = useState(false);
  const [turns, setTurns] = useState<VoiceTurn[]>([]);
  const [error, setError] = useState<string | null>(null);

  const sessionIdRef = useRef<string | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const playbackElRef = useRef<HTMLAudioElement | null>(null);

  const { level, attach } = useLevelMeter();

  const ensureAudioCtx = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext();
    }
    return audioCtxRef.current;
  }, []);

  const connect = useCallback(async () => {
    setError(null);
    setStatus("connecting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      streamRef.current = stream;
      setStatus("running");
      setMode("listening");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Microphone access was denied.",
      );
      setStatus("ended");
    }
  }, []);

  const disconnect = useCallback(() => {
    recorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    playbackElRef.current?.pause();
    attach(null);
    setIsRecording(false);
    setStatus("ended");
  }, [attach]);

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => {
      const next = !prev;
      streamRef.current
        ?.getAudioTracks()
        .forEach((t) => (t.enabled = !next));
      if (next && isRecording) {
        recorderRef.current?.stop();
      }
      return next;
    });
  }, [isRecording]);

  const playResponse = useCallback(
    (audioBlob: Blob) =>
      new Promise<void>((resolve) => {
        const ctx = ensureAudioCtx();
        const url = URL.createObjectURL(audioBlob);
        const el = new Audio(url);
        playbackElRef.current = el;

        const source = ctx.createMediaElementSource(el);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyser.connect(ctx.destination);
        attach(analyser);

        setMode("speaking");
        el.onended = () => {
          attach(null);
          setMode("listening");
          URL.revokeObjectURL(url);
          resolve();
        };
        el.onerror = () => {
          attach(null);
          setMode("listening");
          resolve();
        };
        void el.play();
      }),
    [attach, ensureAudioCtx],
  );

  const startTurn = useCallback(() => {
    if (status !== "running" || isMuted || !streamRef.current) return;
    const ctx = ensureAudioCtx();
    const source = ctx.createMediaStreamSource(streamRef.current);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    attach(analyser);

    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";
    const recorder = new MediaRecorder(streamRef.current, { mimeType });
    chunksRef.current = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = async () => {
      attach(null);
      setIsRecording(false);
      const blob = new Blob(chunksRef.current, { type: mimeType });
      if (blob.size === 0) return;

      setTurns((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "user", label: "Voice message" },
      ]);
      setStatus("connecting");
      try {
        const { audio, sessionId } = await converseWithAudio(
          blob,
          sessionIdRef.current,
        );
        if (sessionId) sessionIdRef.current = sessionId;
        setStatus("running");
        setTurns((prev) => [
          ...prev,
          { id: crypto.randomUUID(), role: "assistant", label: "Reply" },
        ]);
        await playResponse(audio);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Couldn't reach Bunny Buddy.",
        );
        setStatus("running");
        setMode("listening");
      }
    };

    recorderRef.current = recorder;
    recorder.start();
    setIsRecording(true);
    setMode("listening");
  }, [attach, ensureAudioCtx, isMuted, playResponse, status]);

  const stopTurn = useCallback(() => {
    recorderRef.current?.stop();
  }, []);

  /** Tap-to-talk: press to start recording, press again to send. */
  const toggleTurn = useCallback(() => {
    if (isRecording) stopTurn();
    else startTurn();
  }, [isRecording, startTurn, stopTurn]);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      audioCtxRef.current?.close();
    };
  }, []);

  return {
    status,
    isMuted,
    mode,
    isRecording,
    level,
    turns,
    error,
    sessionId: sessionIdRef.current,
    connect,
    disconnect,
    toggleMute,
    toggleTurn,
  };
}
