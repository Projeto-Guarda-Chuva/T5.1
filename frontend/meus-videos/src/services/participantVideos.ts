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
  referenceDate: string,
  videoId?: string,
): Promise<VideoEmailDispatchResponse> {
  const response = await api.post<VideoEmailDispatchResponse>(
    "/participantes/me/video-do-dia/email",
    {
      reference_date: referenceDate,
      video_id: videoId,
    },
  );
  return response.data;
}

export async function getParticipantVideoPlaybackUrl(
  videoId: string,
): Promise<string> {
  const response = await api.get(`/participantes/me/videos/${videoId}/arquivo`, {
    responseType: "blob",
  });

  return URL.createObjectURL(response.data);
}
