import { useState } from "react";
import styles from "./styles.module.css";
import CreateConfigurationModal from "./CreateConfigurationModal";
import ViewConfigurationModal from "./ViewConfigurationModal";
import type { Configuration, CreateConfigurationPayload } from "../../types/configurations";

import { formatDateTime } from "../../utils/format";
import useConfigurations, { CONFIGURATIONS_KEY } from "../../hooks/useConfigurations";
import useDetailsConfigurations from "../../hooks/useDetailsConfigurations";
import useCreateConfiguration from "../../hooks/useCreateConfiguration";
import { useQueryClient } from "@tanstack/react-query";
import useActivateConfiguration from "../../hooks/useActivateConfiguration";

const Parameters = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<Configuration | null>(null);

  const { configurations } = useConfigurations();

  const { configurationDetail } = useDetailsConfigurations(selectedConfig?.id);

  const queryClient = useQueryClient();

  const { createConfiguration } = useCreateConfiguration({
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONFIGURATIONS_KEY] });
    },
  });

  const { activateConfiguration } = useActivateConfiguration({
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONFIGURATIONS_KEY] });
    },
  });

  const handleSetActive = async (id: string): Promise<void> => {
    await activateConfiguration(id);
  };

  const configs = configurations?.items ?? [];

  const handleCreateConfiguration = async (payload: CreateConfigurationPayload) => {
    await createConfiguration(payload);
  };

  return (
    <>
      <div className={`d-flex justify-content-between align-items-center mb-4`}>
        <div>
          <h3 className={styles.headerTitle}>Configurações</h3>
          <p className="text-muted small mb-0">Gerencie e aplique configurações de operação do robô</p>
        </div>

        <button className={`btn btn-primary rounded-pill px-4 fw-semibold ${styles.desktopBtn}`} onClick={() => setIsCreateModalOpen(true)}>
          <i className="bi bi-plus-lg me-2"></i> Nova Configuração
        </button>
      </div>

      <div className="row g-3">
        {configs.map((config) => (
          <div key={config.id} className="col-12 col-md-6 col-lg-4">
            <div className={`card ${styles.paramCard} ${config.is_active ? styles.activeCard : ""}`}>
              <div className="card-body d-flex flex-column">
                <div className="d-flex justify-content-between align-items-start mb-3">
                  <span className={`${styles.idBadge}`}>{config.id}</span>

                  {config.is_active ? (
                    <span className={`badge rounded-pill d-flex align-items-center px-2 py-1 ${styles.activeBadge}`}>
                      <i className="bi bi-check-circle-fill me-1"></i> Ativa
                    </span>
                  ) : (
                    <span className={`badge rounded-pill ${styles.inactiveBadge}`}>Inativa</span>
                  )}
                </div>

                <h6 className={`fw-bold mb-1 ${styles.cardTitle}`}>{config.name}</h6>
                <p className="text-muted small mb-3 flex-grow-1">{config.description}</p>

                <div className={`${styles.dateMeta} mb-3`}>
                  <span>
                    <i className="bi bi-calendar-plus me-1"></i>
                    Criada em {formatDateTime(config.created_at)}
                  </span>
                  <span>
                    <i className="bi bi-pencil me-1"></i>
                    Atualizada em {formatDateTime(config.updated_at)}
                  </span>
                </div>

                <div className={`d-flex gap-2 mt-auto`}>
                  <button className={`btn btn-sm fw-semibold flex-grow-1 ${styles.viewBtn}`} onClick={() => setSelectedConfig(config)}>
                    <i className="bi bi-eye me-1"></i> Ver Detalhes
                  </button>

                  {!config.is_active && (
                    <button className="btn btn-sm fw-semibold flex-grow-1 btn-primary" onClick={() => handleSetActive(config.id)}>
                      <i className="bi bi-play-fill me-1"></i> Aplicar
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <button className={`btn btn-primary ${styles.fab}`} onClick={() => setIsCreateModalOpen(true)} aria-label="Nova configuração">
        <i className="bi bi-plus-lg"></i>
      </button>

      <CreateConfigurationModal isOpen={isCreateModalOpen} onSubmit={handleCreateConfiguration} onClose={() => setIsCreateModalOpen(false)} />

      {selectedConfig && (
        <ViewConfigurationModal
          configDetail={configurationDetail}
          onClose={() => setSelectedConfig(null)}
          onSetActive={async (id) => {
            await handleSetActive(id);
            setSelectedConfig(null);
          }}
        />
      )}
    </>
  );
};

export default Parameters;
