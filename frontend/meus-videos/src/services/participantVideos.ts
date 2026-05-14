import api from "../api";

export interface VideoEmailDispatchResponse {
  dispatch_id: string;
  sent_at: string;
  participant_id: string;
  participant_email: string;
  reference_date: string;
  delivery_mode: "smtp" | "outbox";
  message: string;
}

export async function sendParticipantVideoEmail(
  participantId: string,
  referenceDate: string,
): Promise<VideoEmailDispatchResponse> {
  const response = await api.post<VideoEmailDispatchResponse>(
    `/participantes/${participantId}/video-do-dia/email`,
    {
      reference_date: referenceDate,
    },
  );
  return response.data;
}
