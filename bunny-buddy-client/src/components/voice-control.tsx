import type { FC } from "react";
import { Mic, MicOff, PhoneOff, Loader2 } from "lucide-react";
import { cn } from "../lib/utils";
import type { VoiceOrbState } from "./voice-orb";

export type VoiceSessionStatus = "idle" | "connecting" | "running" | "ended";

export type VoiceControlProps = {
  status: VoiceSessionStatus;
  isMuted: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
  onToggleMute: () => void;
  className?: string;
};

const DOT_COLOR: Record<VoiceSessionStatus, string> = {
  idle: "bg-white/25",
  ended: "bg-white/25",
  connecting: "bg-amber-400 animate-pulse",
  running: "bg-emerald-400",
};

/**
 * Derives the five-state VoiceOrb animation from session status + mute,
 * mirroring assistant-ui's runtime resolution order: idle/ended -> idle;
 * starting -> connecting; muted (even while "speaking") -> muted;
 * otherwise the caller's speaking/listening mode.
 */
export function deriveVoiceOrbState(
  status: VoiceSessionStatus,
  isMuted: boolean,
  mode: "listening" | "speaking",
): VoiceOrbState {
  if (status === "idle" || status === "ended") return "idle";
  if (status === "connecting") return "connecting";
  if (isMuted) return "muted";
  return mode;
}

export const VoiceControl: FC<VoiceControlProps> = ({
  status,
  isMuted,
  onConnect,
  onDisconnect,
  onToggleMute,
  className,
}) => {
  const running = status === "running";
  const connecting = status === "connecting";

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2.5 backdrop-blur-sm",
        className,
      )}
    >
      <span
        aria-hidden
        className={cn("size-2 rounded-full", DOT_COLOR[status])}
      />

      {!running && !connecting && (
        <button
          type="button"
          onClick={onConnect}
          className="text-[13px] font-medium text-white/90 transition hover:text-white"
        >
          Connect
        </button>
      )}

      {connecting && (
        <span className="flex items-center gap-1.5 text-[13px] text-white/60">
          <Loader2 className="size-3.5 animate-spin" />
          Connecting…
        </span>
      )}

      {running && (
        <>
          <button
            type="button"
            onClick={onToggleMute}
            aria-label={isMuted ? "Unmute" : "Mute"}
            aria-pressed={isMuted}
            className={cn(
              "flex size-8 items-center justify-center rounded-full transition",
              isMuted
                ? "bg-white/15 text-white"
                : "text-white/70 hover:bg-white/10 hover:text-white",
            )}
          >
            {isMuted ? (
              <MicOff className="size-4" />
            ) : (
              <Mic className="size-4" />
            )}
          </button>
          <button
            type="button"
            onClick={onDisconnect}
            aria-label="Disconnect"
            className="flex size-8 items-center justify-center rounded-full bg-red-500/90 text-white transition hover:bg-red-500"
          >
            <PhoneOff className="size-3.5" />
          </button>
        </>
      )}
    </div>
  );
};
