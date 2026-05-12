export type OperationStatus = "error" | "success";

export interface OperationLog {
  id: string;
  occurred_at: string;
  duration_seconds: number;
  participant_email: string;
  status: OperationStatus;
  status_text: string;
  description: string;
}

export interface OperationLogResponse {
  items: OperationLog[];
  total: number;
  message: string;
}
