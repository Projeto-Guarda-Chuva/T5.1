import React from "react";

interface InfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  message: string;
  type?: "success" | "error";
}

const InfoModal: React.FC<InfoModalProps> = ({
  isOpen,
  onClose,
  title,
  message,
  type = "success",
}) => {
  if (!isOpen) return null;

  const iconClass =
    type === "success"
      ? "bi bi-check-circle-fill text-success"
      : "bi bi-exclamation-triangle-fill text-danger";

  const buttonClass = type === "success" ? "btn-primary" : "btn-danger";

  return (
    <div
      className="modal d-block"
      style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
      tabIndex={-1}
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content text-center p-4 border-0 shadow-lg rounded-4">
          <div className="modal-body">
            <i className={`${iconClass} display-3 d-block mb-3`}></i>
            <h4 className="fw-bold mb-2">{title}</h4>
            <p className="text-muted mb-4">{message}</p>
            <button
              type="button"
              className={`btn ${buttonClass} w-100 rounded-pill py-2 fw-semibold`}
              onClick={onClose}
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InfoModal;
