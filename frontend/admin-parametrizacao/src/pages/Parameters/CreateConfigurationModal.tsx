import { useState } from "react";
import styles from "./styles.module.css";
import type { CreateConfigurationPayload } from "../../types/configurations";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: CreateConfigurationPayload) => Promise<void>;
}

const DEFAULT_FORM: CreateConfigurationPayload = {
  name: "",
  description: "",
  is_active: false,
  parameters: {
    movement_speed: 1.0,
    movement_duration_seconds: 30,
    video_capture_enabled: false,
    audio_capture_enabled: false,
  },
};

const CreateConfigurationModal = ({ isOpen, onClose, onSubmit }: Props) => {
  const [form, setForm] = useState<CreateConfigurationPayload>(DEFAULT_FORM);

  if (!isOpen) return null;

  const handleChange = (field: keyof CreateConfigurationPayload, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleParamChange = (field: keyof CreateConfigurationPayload["parameters"], value: any) => {
    setForm((prev) => ({
      ...prev,
      parameters: { ...prev.parameters, [field]: value },
    }));
  };

  const handleSubmit = async () => {
    await onSubmit(form);
    setForm(DEFAULT_FORM);
    onClose();
  };

  return (
    <div className={`modal d-block ${styles.modalBackdrop}`} tabIndex={-1} onClick={onClose}>
      <div className={`modal-dialog modal-dialog-centered ${styles.modalDialog}`} onClick={(e) => e.stopPropagation()}>
        <div className={`modal-content ${styles.modalContent}`}>
          <div className={`modal-header ${styles.modalHeader}`}>
            <div>
              <h5 className={`modal-title fw-bold ${styles.modalTitle}`}>Nova Configuração</h5>
              <p className="text-muted small mb-0">Preencha os dados e parâmetros de operação</p>
            </div>
            <button type="button" className={`btn-close ${styles.closeBtn}`} onClick={onClose} aria-label="Fechar" />
          </div>

          <div className="modal-body px-4 pb-2">
            <div className={`${styles.detailSection} mb-4`}>
              <p className={styles.sectionLabel}>
                <i className="bi bi-info-circle me-1"></i> Informações Gerais
              </p>

              <div className="mb-3">
                <label className={`form-label ${styles.formLabel}`}>Nome</label>
                <input
                  type="text"
                  className={`form-control ${styles.formControl}`}
                  placeholder="Ex: Modo Exposição Padrão"
                  value={form.name}
                  onChange={(e) => handleChange("name", e.target.value)}
                />
              </div>

              <div className="mb-0">
                <label className={`form-label ${styles.formLabel}`}>Descrição</label>
                <textarea
                  className={`form-control ${styles.formControl}`}
                  rows={3}
                  placeholder="Descreva o propósito desta configuração..."
                  value={form.description}
                  onChange={(e) => handleChange("description", e.target.value)}
                />
              </div>
            </div>

            <div className={`${styles.detailSection} mb-2`}>
              <p className={styles.sectionLabel}>
                <i className="bi bi-sliders me-1"></i> Parâmetros de Operação
              </p>

              <div className="row g-3">
                <div className="col-12 col-sm-6">
                  <label className={`form-label ${styles.formLabel}`}>
                    <i className="bi bi-speedometer2 me-1"></i> Velocidade (m/s)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="10"
                    className={`form-control ${styles.formControl}`}
                    value={form.parameters.movement_speed}
                    onChange={(e) => handleParamChange("movement_speed", parseFloat(e.target.value))}
                  />
                </div>

                <div className="col-12 col-sm-6">
                  <label className={`form-label ${styles.formLabel}`}>
                    <i className="bi bi-stopwatch me-1"></i> Duração (segundos)
                  </label>
                  <input
                    type="number"
                    min="1"
                    className={`form-control ${styles.formControl}`}
                    value={form.parameters.movement_duration_seconds}
                    onChange={(e) => handleParamChange("movement_duration_seconds", parseInt(e.target.value))}
                  />
                </div>

                <div className="col-12 col-sm-6">
                  <div className={`${styles.toggleCard}`}>
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <p className={`mb-0 fw-semibold ${styles.toggleLabel}`}>
                          <i className="bi bi-camera-video me-2"></i>Captura de Vídeo
                        </p>
                        <p className="mb-0 text-muted" style={{ fontSize: "0.75rem" }}>
                          Habilitar gravação de vídeo
                        </p>
                      </div>
                      <div className="form-check form-switch mb-0">
                        <input
                          className={`form-check-input ${styles.switchInput}`}
                          type="checkbox"
                          role="switch"
                          checked={form.parameters.video_capture_enabled}
                          onChange={(e) => handleParamChange("video_capture_enabled", e.target.checked)}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="col-12 col-sm-6">
                  <div className={`${styles.toggleCard}`}>
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <p className={`mb-0 fw-semibold ${styles.toggleLabel}`}>
                          <i className="bi bi-mic me-2"></i>Captura de Áudio
                        </p>
                        <p className="mb-0 text-muted" style={{ fontSize: "0.75rem" }}>
                          Habilitar gravação de áudio
                        </p>
                      </div>
                      <div className="form-check form-switch mb-0">
                        <input
                          className={`form-check-input ${styles.switchInput}`}
                          type="checkbox"
                          role="switch"
                          checked={form.parameters.audio_capture_enabled}
                          onChange={(e) => handleParamChange("audio_capture_enabled", e.target.checked)}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className={`modal-footer ${styles.modalFooter}`}>
            <button className={`btn fw-semibold ${styles.cancelBtn}`} onClick={onClose}>
              Cancelar
            </button>
            <button className={`btn fw-semibold ${styles.applyBtnModal}`} onClick={handleSubmit} disabled={!form.name.trim()}>
              <i className="bi bi-floppy me-1"></i> Salvar Configuração
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateConfigurationModal;
