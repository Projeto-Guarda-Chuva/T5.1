import { useState } from "react";

interface FormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (time: string) => void;
}

export default function Form({ isOpen, onClose, onSubmit }: FormProps) {
  const [time, setTime] = useState("");
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!time) {
      setError("Por favor, selecione uma hora.");
      return;
    }

    const now = new Date();
    const [hours, minutes] = time.split(":").map(Number);

    const selectedDate = new Date(now);
    selectedDate.setHours(hours, minutes, 0, 0);

    const diffInMs = now.getTime() - selectedDate.getTime();
    let diffInMinutes = diffInMs / (1000 * 60);

    // Tratamento para contornar virada de dia (ex: agora é 00:15 e usuário digita 23:30)
    if (diffInMinutes < -12 * 60) {
      selectedDate.setDate(selectedDate.getDate() - 1);
      diffInMinutes = (now.getTime() - selectedDate.getTime()) / (1000 * 60);
    } else if (diffInMinutes < 0) {
      setError("O horário da participação não pode estar no futuro.");
      return;
    }

    if (diffInMinutes > 60) {
      setError("A participação deve ter ocorrido no máximo há 1 hora.");
      return;
    }

    setError("");
    onSubmit(time);
    setTime(""); // Limpa o estado após confirmar
  };

  return (
    <div
      className="modal d-block"
      style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
      tabIndex={-1}
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content border-0 shadow-lg rounded-4">
          <div className="modal-header border-0 pb-0">
            <h5 className="modal-title fw-bold">Registrar Participação</h5>
            <button
              type="button"
              className="btn-close"
              onClick={onClose}
            ></button>
          </div>
          <div className="modal-body p-4">
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="form-label fw-semibold text-dark">
                  Horário da participação
                </label>
                <input
                  type="time"
                  className={`form-control form-control-lg ${error ? "is-invalid" : ""}`}
                  value={time}
                  onChange={(e) => {
                    setTime(e.target.value);
                    if (error) setError("");
                  }}
                />
                {error && <div className="invalid-feedback">{error}</div>}
              </div>
              <button type="submit" className="btn btn-primary w-100 py-2">
                Confirmar
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
