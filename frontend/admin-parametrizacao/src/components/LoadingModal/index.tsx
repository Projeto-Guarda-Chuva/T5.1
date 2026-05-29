import styles from "./styles.module.css";

type LoadingModalProps = {
  isOpen: boolean;
};

const LoadingModal = ({ isOpen }: LoadingModalProps) => {
  if (!isOpen) return null;

  return (
    <div className={styles.loadingOverlay}>
      <div className={`spinner-border ${styles.spinnerCustom}`} role="status">
        <span className="visually-hidden">Carregando...</span>
      </div>
    </div>
  );
};

export default LoadingModal;
