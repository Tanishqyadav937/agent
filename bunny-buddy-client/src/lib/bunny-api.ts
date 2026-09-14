// Talks to the Bunny Buddy backend described in the architecture doc:
//   POST /converse       multipart audio -> WAV audio (+ X-Session-ID header)
//   POST /converse-text   { sessionId?, message } -> WAV audio (+ X-Session-ID header)
//   GET  /health

const BASE_URL = import.meta.env.VITE_BUNNY_API_URL ?? "http://localhost:3000";

export type ConverseResult = {
  audio: Blob;
  sessionId: string | null;
};

async function unwrapAudioResponse(res: Response): Promise<ConverseResult> {
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(
      `Bunny Buddy backend returned ${res.status}${detail ? `: ${detail}` : ""}`,
    );
  }
  const audio = await res.blob();
  const sessionId = res.headers.get("X-Session-ID");
  return { audio, sessionId };
}

/** Send a recorded utterance (webm/opus from MediaRecorder) to /converse. */
export async function converseWithAudio(
  audioBlob: Blob,
  sessionId: string | null,
): Promise<ConverseResult> {
  const form = new FormData();
  form.append("audio", audioBlob, "utterance.webm");
  if (sessionId) form.append("sessionId", sessionId);

  const res = await fetch(`${BASE_URL}/converse`, {
    method: "POST",
    body: form,
    headers: sessionId ? { "X-Session-ID": sessionId } : undefined,
  });
  return unwrapAudioResponse(res);
}

/** Text-input fallback, useful for debugging without a mic. */
export async function converseWithText(
  message: string,
  sessionId: string | null,
): Promise<ConverseResult> {
  const res = await fetch(`${BASE_URL}/converse-text`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(sessionId ? { "X-Session-ID": sessionId } : {}),
    },
    body: JSON.stringify({ message, sessionId }),
  });
  return unwrapAudioResponse(res);
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
