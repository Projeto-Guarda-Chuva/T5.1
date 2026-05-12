import useCurrentActiveConfiguration from "../../hooks/useCurrentActiveConfiguration";
import ActiveConfigurationCard from "./CurrentConfigurationCard";
import styles from "./styles.module.css";

const Home = () => {
  const { currentConfiguration } = useCurrentActiveConfiguration();

  const currentConfigData = currentConfiguration?.configuration;

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h4 className="fw-bold mb-0">Visão Geral</h4>
          <p className="text-muted small mb-0">Bem-vindo, Administrador</p>
        </div>
      </div>

      <div className="row g-3">
        <div className="col-12 col-md-6">
          <div className={`card ${styles.dashboardCard}`}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-start mb-3">
                <h6 className="card-subtitle text-muted fw-semibold">Status da Água-viva</h6>
                <span className={`${styles.statusIndicator} ${styles.statusOnline}`}></span>
              </div>
              <h3 className="fw-bold mb-1">Operacional</h3>
              <p className="small text-success mb-3">Nenhuma anomalia detectada</p>

              <button className={`btn btn-danger w-100 py-2 ${styles.btnEmergency}`}>
                <i className="bi bi-stop-octagon-fill me-2"></i>
                PARADA DE EMERGÊNCIA
              </button>
            </div>
          </div>
        </div>

        <div className="col-12 col-md-6">
          <ActiveConfigurationCard currentConfiguration={currentConfigData} />
        </div>

        <div className="col-12">
          <div className={`card ${styles.dashboardCard}`}>
            <div className="card-body p-0">
              <div className="p-3 border-bottom d-flex justify-content-between align-items-center">
                <h6 className="mb-0 fw-bold">Jornadas Recentes</h6>
                <a href="#" className="text-decoration-none small text-primary fw-semibold">
                  Ver tudo
                </a>
              </div>

              <div className="list-group list-group-flush rounded-bottom">
                <div className={`list-group-item border-0 py-3 ${styles.historyItem}`}>
                  <div className="d-flex w-100 justify-content-between align-items-center">
                    <div>
                      <h6 className="mb-1 fw-semibold">Gravação #1042</h6>
                      <small className="text-muted d-block">
                        <i className="bi bi-clock me-1"></i> Hoje, 14:30 - Duração: 05m 12s
                      </small>
                    </div>
                    <span className="badge bg-success rounded-pill">Concluído</span>
                  </div>
                </div>

                <div className={`list-group-item border-0 py-3 ${styles.historyItem}`}>
                  <div className="d-flex w-100 justify-content-between align-items-center">
                    <div>
                      <h6 className="mb-1 fw-semibold">Gravação #1041</h6>
                      <small className="text-muted d-block">
                        <i className="bi bi-clock me-1"></i> Hoje, 13:15 - Duração: 03m 45s
                      </small>
                    </div>
                    <span className="badge bg-success rounded-pill">Concluído</span>
                  </div>
                </div>

                <div className={`list-group-item border-0 py-3 ${styles.historyItem}`}>
                  <div className="d-flex w-100 justify-content-between align-items-center">
                    <div>
                      <h6 className="mb-1 fw-semibold text-danger">Gravação #1040</h6>
                      <small className="text-muted d-block">
                        <i className="bi bi-exclamation-triangle me-1"></i> Ontem, 18:00 - Interrompido
                      </small>
                    </div>
                    <span className="badge bg-danger rounded-pill">Anomalia</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Home;
