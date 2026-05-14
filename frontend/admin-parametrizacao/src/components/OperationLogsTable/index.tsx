import type { OperationLogResponse } from "../../types/operationLogs";

import OperationLogsRow from "./OperationLogsRow";
import styles from "./styles.module.css";

interface OperationLogsTableProps {
  operationLogs: OperationLogResponse | undefined | null;
}

const OperationLogsTable = ({ operationLogs }: OperationLogsTableProps) => {
  const items = operationLogs?.items;

  return (
    <table className={`table table-hover mb-0 ${styles.responsiveTable}`}>
      <thead className="table-light">
        <tr>
          <th scope="col" className="ps-4">
            ID Sessão
          </th>
          <th scope="col">Data / Hora</th>
          <th scope="col">Duração</th>
          <th scope="col">Participante (E-mail)</th>
          <th scope="col">Status</th>
        </tr>
      </thead>
      <tbody>{items && items.map((log) => <OperationLogsRow key={log.id} log={log} />)}</tbody>
    </table>
  );
};

export default OperationLogsTable;
