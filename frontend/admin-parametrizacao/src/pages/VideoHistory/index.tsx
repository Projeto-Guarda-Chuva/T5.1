import OperationLogsTable from "../../components/OperationLogsTable";
import useOperationLog from "../../hooks/useOperationLog";
import styles from "./styles.module.css";

const VideoHistory = () => {
  const { operationLogs } = useOperationLog();

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className={styles.headerTitle}>Log de Sessões</h3>
          <p className="text-muted small mb-0">Histórico de operações e gravações da Água-viva</p>
        </div>

        <button className="btn btn-outline-secondary rounded-pill btn-sm d-none d-md-flex align-items-center">
          <i className="bi bi-funnel me-2"></i> Filtrar
        </button>
      </div>

      <div className={`card ${styles.logCard}`}>
        <div className="card-body p-0">
          <div className="table-responsive">
            <OperationLogsTable operationLogs={operationLogs} />
          </div>

          <div className="card-footer bg-white border-top p-3 d-flex justify-content-between align-items-center">
            <span className="text-muted small">Exibindo 4 registros</span>
            <nav aria-label="Navegação de páginas de log">
              <ul className="pagination pagination-sm mb-0">
                <li className="page-item disabled">
                  <a className="page-link" href="#" tabIndex={-1}>
                    Anterior
                  </a>
                </li>
                <li className="page-item active">
                  <a className="page-link" href="#">
                    1
                  </a>
                </li>
                <li className="page-item">
                  <a className="page-link" href="#">
                    2
                  </a>
                </li>
                <li className="page-item">
                  <a className="page-link" href="#">
                    Próxima
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </div>
    </>
  );
};

export default VideoHistory;
