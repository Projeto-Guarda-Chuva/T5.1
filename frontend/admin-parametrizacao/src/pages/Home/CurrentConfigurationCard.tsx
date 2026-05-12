import styles from "./styles.module.css";
import type { Configuration } from "../../types/configurations";

interface ActiveConfigurationCardProps {
  currentConfiguration: Configuration | undefined;
}

const ActiveConfigurationCard = ({ currentConfiguration }: ActiveConfigurationCardProps) => {
  return (
    <div className={`card ${styles.dashboardCard}`}>
      <div className="card-body d-flex flex-column">
        <h6 className="card-subtitle text-muted fw-semibold mb-3">Parametrização Ativa</h6>

        {currentConfiguration ? (
          <>
            <div className="d-flex align-items-center mb-3">
              <div className={`bg-primary bg-opacity-10 text-primary ${styles.iconWrapper} me-3`}>
                <i className="bi bi-sliders"></i>
              </div>
              <div>
                <h6 className="mb-0 fw-bold">{currentConfiguration.name}</h6>
                <small className="text-muted">{currentConfiguration.description}</small>
              </div>
            </div>

            {currentConfiguration.parameters && (
              <div className="row g-2 mb-3">
                <div className="col-6">
                  <div className="bg-light rounded p-2 text-center">
                    <small className="text-muted d-block">Velocidade</small>
                    <span className="fw-bold">{currentConfiguration.parameters.movement_speed}</span>
                  </div>
                </div>
                <div className="col-6">
                  <div className="bg-light rounded p-2 text-center">
                    <small className="text-muted d-block">Duração</small>
                    <span className="fw-bold">{currentConfiguration.parameters.movement_duration_seconds}s</span>
                  </div>
                </div>
                <div className="col-6">
                  <div
                    className={`rounded p-2 text-center ${currentConfiguration.parameters.video_capture_enabled ? "bg-success bg-opacity-10" : "bg-light"}`}
                  >
                    <small className="text-muted d-block">Vídeo</small>
                    <i
                      className={`bi ${currentConfiguration.parameters.video_capture_enabled ? "bi-camera-video-fill text-success" : "bi-camera-video-off text-muted"}`}
                    ></i>
                  </div>
                </div>
                <div className="col-6">
                  <div
                    className={`rounded p-2 text-center ${currentConfiguration.parameters.audio_capture_enabled ? "bg-success bg-opacity-10" : "bg-light"}`}
                  >
                    <small className="text-muted d-block">Áudio</small>
                    <i
                      className={`bi ${currentConfiguration.parameters.audio_capture_enabled ? "bi-mic-fill text-success" : "bi-mic-mute text-muted"}`}
                    ></i>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="d-flex flex-column align-items-center justify-content-center py-3 text-center flex-grow-1">
            <div className={`bg-secondary bg-opacity-10 text-secondary ${styles.iconWrapper} mb-2`}>
              <i className="bi bi-sliders"></i>
            </div>
            <p className="text-muted small mb-0">Nenhuma configuração ativa</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveConfigurationCard;
