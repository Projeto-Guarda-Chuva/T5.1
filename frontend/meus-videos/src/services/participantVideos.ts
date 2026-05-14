export interface VideoEmailDispatchResponse {
  dispatch_id: string;
  sent_at: string;
  participant_id: string;
  participant_email: string;
  reference_date: string;
  delivery_mode: "smtp" | "outbox";
  message: string;
}

const API_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://127.0.0.1:8001";

export async function sendParticipantVideoEmail(
  participantId: string,
  referenceDate: string,
): Promise<VideoEmailDispatchResponse> {
  const response = await fetch(
    `${API_BASE_URL}/participantes/${participantId}/video-do-dia/email`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        reference_date: referenceDate,
      }),
    },
  );

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      payload?.detail || "Não foi possível enviar o vídeo por e-mail.",
    );
  }

  return payload as VideoEmailDispatchResponse;
}
