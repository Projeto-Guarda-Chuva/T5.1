import styles from "./CreateParameterModal.module.css";

type CreateParameterModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

const CreateParameterModal = ({ isOpen, onClose }: CreateParameterModalProps) => {
  if (!isOpen) return null;

  return (
    <>
      <div className={styles.modalBackdrop} onClick={onClose}></div>

      <div className={`modal fade show ${styles.modalContainer}`} tabIndex={-1} aria-hidden="true">
        <div className="modal-dialog modal-dialog-centered modal-dialog-scrollable">
          <div className={`modal-content ${styles.modalContentCard}`}>
            <div className="modal-header border-0 pb-0 pt-4 px-4">
              <div>
                <h5 className="modal-title fw-bold">Novo Parâmetro</h5>
                <p className="text-muted small mb-0">Defina um comportamento para a Água-viva</p>
              </div>
              <button type="button" className="btn-close" onClick={onClose} aria-label="Fechar"></button>
            </div>

            <div className="modal-body px-4 pt-3 pb-4">
              <div className="alert alert-warning py-2 d-flex align-items-center small mb-4" role="alert">
                <i className="bi bi-shield-lock-fill fs-5 me-3 text-warning"></i>
                <div>
                  <strong>Atenção:</strong> Por motivos de segurança na operação, este parâmetro <b>não poderá ser alterado</b> após o cadastro.
                </div>
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  onClose();
                }}
              >
                <div className="form-floating mb-3">
                  <input type="text" className={`form-control ${styles.customRounded}`} id="paramName" placeholder="Nome" required />
                  <label htmlFor="paramName">Nome (ex: Velocidade Base)</label>
                </div>

                <div className="form-floating mb-3">
                  <select className={`form-select ${styles.customRounded}`} id="paramType" aria-label="Tipo" required>
                    <option value="">Selecione o tipo</option>
                    <option value="1">Movimento / Físico</option>
                    <option value="2">Iluminação / Visual</option>
                    <option value="3">Sistema / Segurança</option>
                  </select>
                  <label htmlFor="paramType">Categoria</label>
                </div>

                <div className="form-floating mb-4">
                  <input type="text" className={`form-control ${styles.customRounded}`} id="paramValue" placeholder="Valor" required />
                  <label htmlFor="paramValue">Valor Padrão (ex: 2.5 m/s)</label>
                </div>

                <div className="d-grid gap-2 mt-2">
                  <button type="submit" className="btn btn-primary py-3 fw-bold rounded-3">
                    <i className="bi bi-check2-circle me-2"></i>
                    Cadastrar Parâmetro Definitivo
                  </button>
                  <button type="button" className="btn btn-light py-2 fw-semibold rounded-3 text-muted" onClick={onClose}>
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default CreateParameterModal;
