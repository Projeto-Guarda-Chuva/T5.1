import styles from "./styles.module.css";

type ErrorModalProps = {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message: string;
};

const ErrorModal = ({ isOpen, onClose, title = "Ocorreu um Erro", message }: ErrorModalProps) => {
  if (!isOpen) return null;

  return (
    <>
      <div className={styles.modalBackdrop} onClick={onClose}></div>

      <div className={`modal fade show ${styles.modalContainer}`} tabIndex={-1} aria-hidden="true">
        <div className="modal-dialog modal-dialog-centered">
          <div className={`modal-content text-center p-3 p-md-4 ${styles.modalCard}`}>
            <div className="modal-body pt-4">
              <i className={`bi bi-exclamation-octagon-fill text-danger d-block mb-3 ${styles.iconWrapper}`}></i>

              <h4 className="fw-bold mb-2">{title}</h4>
              <p className="text-muted mb-4">{message}</p>

              <button type="button" className="btn btn-danger w-100 rounded-pill py-2 fw-semibold" onClick={onClose}>
                Tentar Novamente
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ErrorModal;
