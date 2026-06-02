import styles from "./styles.module.css";

import type { OperationLog } from "../../types/operationLogs";
import { formatDateTime } from "../../utils/format";

interface OperationLogsRowProps {
  log: OperationLog;
}

const OperationLogsRow = ({ log }: OperationLogsRowProps) => {
  return (
    <tr key={log.id}>
      <td data-label="ID Sessão" className="ps-md-4 fw-semibold text-primary">
        {log.id}
      </td>

      <td data-label="Data / Hora" className="text-muted">
        {formatDateTime(log.occurred_at)}
      </td>

      <td data-label="Duração">{log.duration_seconds}</td>

      <td data-label="Participante">{log.participant_email}</td>

      <td data-label="Status">
        <div className="d-flex align-items-center justify-content-end justify-content-md-start">
          {log.status === "success" ? (
            <>
              <div className={`bg-success bg-opacity-10 text-success me-2 ${styles.statusIcon}`}>
                <i className="bi bi-check-lg"></i>
              </div>
              <span className="fw-semibold text-success d-none d-md-inline">{log.status_text}</span>
            </>
          ) : (
            <>
              <div className={`bg-danger bg-opacity-10 text-danger me-2 ${styles.statusIcon}`}>
                <i className="bi bi-exclamation-triangle-fill"></i>
              </div>
              <span className="fw-semibold text-danger d-none d-md-inline">{log.status_text}</span>
            </>
          )}
          <span className={`fw-semibold d-md-none ms-2 ${log.status === "success" ? "text-success" : "text-danger"}`}>{log.status_text}</span>
        </div>
      </td>
    </tr>
  );
};

export default OperationLogsRow;
