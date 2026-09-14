import { VoiceOrb } from "./components/voice-orb";
import { VoiceControl, deriveVoiceOrbState } from "./components/voice-control";
import { useBunnyVoiceSession } from "./hooks/use-bunny-voice-session";

const HINT: Record<string, string> = {
  idle: "Connect to start talking with Elyra",
  ended: "Connect to start talking with Elyra",
  connecting: "One sec…",
};

export default function App() {
  const {
    status,
    isMuted,
    mode,
    isRecording,
    level,
    turns,
    error,
    connect,
    disconnect,
    toggleMute,
    toggleTurn,
  } = useBunnyVoiceSession();

  const orbState = deriveVoiceOrbState(status, isMuted, mode);
  const running = status === "running";

  const hint =
    HINT[status] ??
    (isMuted
      ? "Mic muted"
      : mode === "speaking"
        ? "Elyra is replying…"
        : isRecording
          ? "Listening — tap the orb to send"
          : "Tap the orb to talk");

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-8 bg-[#1c1622] px-6 text-white">
      <div className="flex flex-col items-center gap-1 text-center">
        <div className="flex items-center gap-2">
          <img 
            src="/assistant.png" 
            alt="Assistant" 
            className="w-6 h-6"
          />
          <h1 className="font-serif text-xl tracking-tight text-white/90">
            Elyra
          </h1>
        </div>
        <p className="text-[13px] text-white/40">{hint}</p>
      </div>

      <button
        type="button"
        onClick={toggleTurn}
        disabled={!running || isMuted}
        aria-label={isRecording ? "Stop and send" : "Start talking"}
        className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-white/30 disabled:cursor-default"
      >
        <VoiceOrb
          state={orbState}
          volume={level}
          variant="violet"
          className="size-40 transition-transform duration-200 active:scale-95"
        />
      </button>

      <VoiceControl
        status={status}
        isMuted={isMuted}
        onConnect={connect}
        onDisconnect={disconnect}
        onToggleMute={toggleMute}
      />

      {error && (
        <p className="max-w-xs text-center text-[13px] text-red-300/90">
          {error}
        </p>
      )}

      {turns.length > 0 && (
        <ul className="flex w-full max-w-xs flex-col gap-1 text-[12px] text-white/35">
          {turns.slice(-4).map((t) => (
            <li key={t.id} className="flex gap-2">
              <span className="w-14 shrink-0 text-white/25">
                {t.role === "user" ? "you" : "elyra"}
              </span>
              <span>{t.label}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
