import { useState } from "react";
import styles from "./styles.module.css";
import CreateParameterModal from "./CreateParameterModal";

const MOCK_PARAMETERS = [
  {
    id: 1,
    name: "Perfil Interativo (Padrão)",
    category: "Movimento / Iluminação",
    badgeClass: "bg-primary text-primary",
    value: "Velocidade: 2.0 m/s | LED: Azul Turquesa",
  },
  {
    id: 2,
    name: "Modo Fuga (Rápido)",
    category: "Movimento",
    badgeClass: "bg-danger text-danger",
    value: "Velocidade: 4.5 m/s | LED: Desligado",
  },
  {
    id: 3,
    name: "Modo Manutenção",
    category: "Sistema",
    badgeClass: "bg-secondary text-secondary",
    value: "Velocidade: 0.0 m/s (Parado) | LED: Laranja Pisca",
  },
];

const Parameters = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeParamId, setActiveParamId] = useState<number>(1);

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className={styles.headerTitle}>Parâmetros</h3>
          <p className="text-muted small mb-0">Selecione a configuração atual do robô</p>
        </div>

        <button className={`btn btn-primary rounded-pill px-4 fw-semibold ${styles.desktopBtn}`} onClick={() => setIsModalOpen(true)}>
          <i className="bi bi-plus-lg me-2"></i> Novo Parâmetro
        </button>
      </div>

      <div className="row g-3">
        {MOCK_PARAMETERS.map((param) => {
          const isActive = activeParamId === param.id;

          return (
            <div key={param.id} className="col-12 col-md-6 col-lg-4">
              <div className={`card ${styles.paramCard} ${isActive ? styles.activeCard : ""}`}>
                <div className="card-body d-flex flex-column">
                  {/* Topo do Card */}
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <span className={`badge bg-opacity-10 ${param.badgeClass}`}>{param.category}</span>

                    {isActive ? (
                      <span className="badge bg-primary rounded-pill d-flex align-items-center px-2 py-1">
                        <i className="bi bi-check-circle-fill me-1"></i> Ativo Atual
                      </span>
                    ) : (
                      <i className={`bi bi-lock-fill ${styles.lockIcon}`} title="Parâmetro imutável"></i>
                    )}
                  </div>

                  <h6 className="fw-bold mb-1">{param.name}</h6>
                  <p className="text-muted small mb-3 flex-grow-1">{param.value}</p>

                  {!isActive && (
                    <button className="btn btn-outline-primary btn-sm w-100 fw-semibold mt-auto rounded-3" onClick={() => setActiveParamId(param.id)}>
                      <i className="bi bi-play-fill me-1"></i> Aplicar Parâmetro
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <button className={`btn btn-primary ${styles.fab}`} onClick={() => setIsModalOpen(true)} aria-label="Adicionar novo parâmetro">
        <i className="bi bi-plus-lg"></i>
      </button>

      <CreateParameterModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
};

export default Parameters;
