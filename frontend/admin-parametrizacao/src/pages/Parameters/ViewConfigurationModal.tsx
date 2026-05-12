import styles from "./styles.module.css";
import type { Configuration, ConfigurationParameters } from "../../types/configurations";
import { formatDateTime } from "../../utils/format";

interface Props {
  configDetail: Configuration | undefined;
  onClose: () => void;
  onSetActive: (id: string) => Promise<void>;
}

const ViewConfigurationModal = ({ configDetail, onClose, onSetActive }: Props) => {
  const config = configDetail;

  if (!config) return null;

  const params: ConfigurationParameters | undefined = config.parameters;

  return (
    <div className={`modal d-block ${styles.modalBackdrop}`} tabIndex={-1} onClick={onClose}>
      <div className={`modal-dialog modal-dialog-centered ${styles.modalDialog}`} onClick={(e) => e.stopPropagation()}>
        <div className={`modal-content ${styles.modalContent}`}>
          <div className={`modal-header ${styles.modalHeader}`}>
            <div>
              <span className={styles.idBadge}>{config.id}</span>
              <h5 className={`modal-title fw-bold mt-2 ${styles.modalTitle}`}>{config.name}</h5>
            </div>
            <button type="button" className={`btn-close ${styles.closeBtn}`} onClick={onClose} aria-label="Fechar" />
          </div>

          <div className="modal-body px-4 pb-2">
            <div className="mb-4">
              {config.is_active ? (
                <span className={`badge rounded-pill ${styles.activeBadge}`}>
                  <i className="bi bi-check-circle-fill me-1"></i> Configuração Ativa
                </span>
              ) : (
                <span className={`badge rounded-pill ${styles.inactiveBadge}`}>Inativa</span>
              )}
            </div>

            <div className={`${styles.detailSection} mb-4`}>
              <p className={styles.sectionLabel}>
                <i className="bi bi-file-text me-1"></i> Descrição
              </p>
              <p className="text-muted small mb-0">{config.description}</p>
            </div>

            <div className={`${styles.detailSection} mb-4`}>
              <p className={styles.sectionLabel}>
                <i className="bi bi-clock-history me-1"></i> Histórico
              </p>
              <div className="row g-2">
                <div className="col-6">
                  <div className={styles.metaBox}>
                    <span className={styles.metaBoxLabel}>Criada em</span>
                    <span className={styles.metaBoxValue}>{formatDateTime(config.created_at)}</span>
                  </div>
                </div>
                <div className="col-6">
                  <div className={styles.metaBox}>
                    <span className={styles.metaBoxLabel}>Atualizada em</span>
                    <span className={styles.metaBoxValue}>{formatDateTime(config.updated_at)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className={`${styles.detailSection} mb-2`}>
              <p className={styles.sectionLabel}>
                <i className="bi bi-sliders me-1"></i> Parâmetros de Operação
              </p>

              <div className="row g-2">
                <div className="col-6">
                  <div className={styles.paramBox}>
                    <i className={`bi bi-speedometer2 ${styles.paramIcon}`}></i>
                    <span className={styles.paramBoxLabel}>Velocidade de Movimento</span>
                    <span className={styles.paramBoxValue}>{params?.movement_speed} m/s</span>
                  </div>
                </div>

                <div className="col-6">
                  <div className={styles.paramBox}>
                    <i className={`bi bi-stopwatch ${styles.paramIcon}`}></i>
                    <span className={styles.paramBoxLabel}>Duração do Movimento</span>
                    <span className={styles.paramBoxValue}>{params?.movement_duration_seconds}s</span>
                  </div>
                </div>

                <div className="col-6">
                  <div className={`${styles.paramBox} ${params?.video_capture_enabled ? styles.paramEnabled : styles.paramDisabled}`}>
                    <i className={`bi bi-camera-video ${styles.paramIcon}`}></i>
                    <span className={styles.paramBoxLabel}>Captura de Vídeo</span>
                    <span className={styles.paramBoxValue}>
                      {params?.video_capture_enabled ? (
                        <>
                          <i className="bi bi-check-circle-fill text-success me-1"></i>Ativada
                        </>
                      ) : (
                        <>
                          <i className="bi bi-x-circle-fill text-danger me-1"></i>Desativada
                        </>
                      )}
                    </span>
                  </div>
                </div>

                <div className="col-6">
                  <div className={`${styles.paramBox} ${params?.audio_capture_enabled ? styles.paramEnabled : styles.paramDisabled}`}>
                    <i className={`bi bi-mic ${styles.paramIcon}`}></i>
                    <span className={styles.paramBoxLabel}>Captura de Áudio</span>
                    <span className={styles.paramBoxValue}>
                      {params?.audio_capture_enabled ? (
                        <>
                          <i className="bi bi-check-circle-fill text-success me-1"></i>Ativada
                        </>
                      ) : (
                        <>
                          <i className="bi bi-x-circle-fill text-danger me-1"></i>Desativada
                        </>
                      )}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className={`modal-footer ${styles.modalFooter}`}>
            <button className={`btn fw-semibold ${styles.cancelBtn}`} onClick={onClose}>
              Fechar
            </button>

            {!config.is_active && (
              <button className={`btn fw-semibold btn-primary`} onClick={async () => await onSetActive(config.id)}>
                <i className="bi bi-play-fill me-1"></i> Aplicar Configuração
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ViewConfigurationModal;
