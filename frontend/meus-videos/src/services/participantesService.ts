import api from "../api";

export interface AceiteTermo {
  aceitou: boolean;
  versao_termo: string;
}

export interface AtualizarStatus {
  status_gravacao: "ja_participei" | "ainda_participarei";
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

export default {
  aceitarTermo,
  atualizarStatus,
};
