import api from "../api";

export interface ParticipantResponse {
  id: string;
  name: string;
  email: string;
}

export interface AceiteTermo {
  aceitou: boolean;
  versao_termo: string;
}

export interface AtualizarStatus {
  status_gravacao: "ja_participei" | "ainda_participarei";
}

export interface ParticipationEventResponse {
  participant_id: string;
  participant_email: string;
  event_type: "will_participate" | "already_participated";
  recorded_at: string;
  associated_video_ids: string[];
  associated_videos_count: number;
  message: string;
}

const aceitarTermo = async (participanteId: string, aceite: AceiteTermo) => {
  const response = await api.patch(
    `/participantes/${participanteId}/aceite-termo`,
    aceite,
  );
  return response.data;
};

const atualizarStatus = async (
  participanteId: string,
  status: AtualizarStatus,
) => {
  const response = await api.patch(
    `/participantes/${participanteId}/status`,
    status,
  );
  return response.data;
};

const marcarQueVaiParticipar = async (): Promise<ParticipationEventResponse> => {
  const response = await api.post<ParticipationEventResponse>(
    "/participantes/me/ainda-vou-participar",
  );
  return response.data;
};

const marcarQueJaParticipou = async (): Promise<ParticipationEventResponse> => {
  const response = await api.post<ParticipationEventResponse>(
    "/participantes/me/ja-participei",
  );
  return response.data;
};

const getCurrentParticipant = async (): Promise<ParticipantResponse> => {
  const response = await api.get<ParticipantResponse>("/participantes/me");
  return response.data;
};

export default {
  aceitarTermo,
  atualizarStatus,
  marcarQueVaiParticipar,
  marcarQueJaParticipou,
  getCurrentParticipant,
};
