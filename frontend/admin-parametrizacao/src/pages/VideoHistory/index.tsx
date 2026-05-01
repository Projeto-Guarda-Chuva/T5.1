import styles from "./styles.module.css";

const SESSION_LOGS = [
  {
    id: "SESS-1042",
    date: "01/05/2026 14:30",
    duration: "05m 12s",
    status: "success",
    statusText: "Concluído",
    participantEmail: "usuario1@exemplo.com",
  },
  {
    id: "SESS-1041",
    date: "01/05/2026 13:15",
    duration: "03m 45s",
    status: "success",
    statusText: "Concluído",
    participantEmail: "visitante_02@exemplo.com",
  },
  {
    id: "SESS-1040",
    date: "30/04/2026 18:00",
    duration: "01m 10s",
    status: "error",
    statusText: "Interrompido (Anomalia)",
    participantEmail: "teste_ops@exemplo.com",
  },
  {
    id: "SESS-1039",
    date: "30/04/2026 17:20",
    duration: "04m 00s",
    status: "success",
    statusText: "Concluído",
    participantEmail: "maria.silva@exemplo.com",
  },
];

const VideoHistory = () => {
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
              <tbody>
                {SESSION_LOGS.map((log) => (
                  <tr key={log.id}>
                    <td data-label="ID Sessão" className="ps-md-4 fw-semibold text-primary">
                      {log.id}
                    </td>

                    <td data-label="Data / Hora" className="text-muted">
                      {log.date}
                    </td>

                    <td data-label="Duração">{log.duration}</td>

                    <td data-label="Participante">{log.participantEmail}</td>

                    <td data-label="Status">
                      <div className="d-flex align-items-center justify-content-end justify-content-md-start">
                        {log.status === "success" ? (
                          <>
                            <div className={`bg-success bg-opacity-10 text-success me-2 ${styles.statusIcon}`}>
                              <i className="bi bi-check-lg"></i>
                            </div>
                            <span className="fw-semibold text-success d-none d-md-inline">{log.statusText}</span>
                          </>
                        ) : (
                          <>
                            <div className={`bg-danger bg-opacity-10 text-danger me-2 ${styles.statusIcon}`}>
                              <i className="bi bi-exclamation-triangle-fill"></i>
                            </div>
                            <span className="fw-semibold text-danger d-none d-md-inline">{log.statusText}</span>
                          </>
                        )}
                        <span className={`fw-semibold d-md-none ms-2 ${log.status === "success" ? "text-success" : "text-danger"}`}>
                          {log.statusText}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
