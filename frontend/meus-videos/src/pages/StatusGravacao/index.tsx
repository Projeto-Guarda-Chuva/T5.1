import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../../utils/routes";
import participantesService from "../../services/participantesService";

export default function StatusGravacao() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!status) {
      alert("Por favor, selecione uma opção!");
      return;
    }

    try {
      setLoading(true);
      const loggedUser = JSON.parse(
        localStorage.getItem("logged_user") || "{}",
      );
      if (loggedUser.email) {
        loggedUser.status_gravacao = status;
        localStorage.setItem("logged_user", JSON.stringify(loggedUser));
      }

      await participantesService.atualizarStatus("123", {
        status_gravacao: status as "ja_participei" | "ainda_participarei",
      });

      alert(`Status registrado! Redirecionando...`);
      navigate(ROUTES.HOME);
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        "Erro ao registrar status. Tente novamente.";
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container d-flex align-items-center justify-content-center flex-grow-1">
      <div
        className="card shadow-sm w-100"
        style={{ maxWidth: "500px", borderRadius: "16px" }}
      >
        <div className="card-body p-5 text-center">
          <h3 className="mb-4">Falta pouco!</h3>
          <p className="text-muted mb-4">
            Para organizarmos seus vídeos, nos diga:
          </p>

          <form onSubmit={handleSubmit}>
            <div className="d-grid gap-3 mb-4">
              <button
                type="button"
                className={`btn btn-lg ${status === "ja_participei" ? "btn-primary" : "btn-outline-primary"}`}
                onClick={() => setStatus("ja_participei")}
              >
                Já participei da gravação
              </button>

              <button
                type="button"
                className={`btn btn-lg ${status === "ainda_participarei" ? "btn-primary" : "btn-outline-primary"}`}
                onClick={() => setStatus("ainda_participarei")}
              >
                Ainda participarei da gravação
              </button>
            </div>

            <button
              type="submit"
              className="btn btn-success w-100"
              disabled={!status || loading}
            >
              {loading ? "Enviando..." : "Confirmar e Acessar"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
