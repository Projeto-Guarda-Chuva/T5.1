import api from "../api";
import type { OperationLogResponse } from "../types/operationLogs";

const getOperationLogs = async (): Promise<OperationLogResponse | null> => {
  const response = await api.get("/operation-logs");

  return response.data ?? null;
};

export default {
  getOperationLogs,
};
