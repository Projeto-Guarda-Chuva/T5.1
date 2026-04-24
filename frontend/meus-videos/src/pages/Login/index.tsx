import { useState } from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "../../utils/routes";

export default function AuthPage() {
  const [activeTab, setActiveTab] = useState<"login" | "cadastro">("login");

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const [regNome, setRegNome] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConsentimento, setRegConsentimento] = useState(false);

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleTabSwitch = (tab: "login" | "cadastro") => {
    setActiveTab(tab);
    setErrors({});
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    if (!loginEmail) newErrors.loginEmail = "O e-mail é obrigatório.";
    if (!loginPassword) newErrors.loginPassword = "A senha é obrigatória.";
    setErrors(newErrors);
  };

  const handleCadastro = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    if (!regNome) newErrors.regNome = "O nome é obrigatório.";
    if (!regEmail) newErrors.regEmail = "O e-mail é obrigatório.";
    if (!regPassword) newErrors.regPassword = "A senha é obrigatória.";
    if (!regConsentimento)
      newErrors.regConsentimento =
        "Você deve aceitar o termo de consentimento.";
    setErrors(newErrors);
  };

  return (
    <div className="container d-flex align-items-center justify-content-center flex-grow-1">
      <style>{`
        .fade-in {
          animation: fadeIn 0.3s ease-in-out;
        }
        @keyframes fadeIn {
          0% { opacity: 0; transform: translateY(10px); }
          100% { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div
        className="card shadow-sm w-100"
        style={{ maxWidth: "420px", borderRadius: "16px" }}
      >
        <div className="card-body p-4">
          <ul className="nav nav-tabs mb-4">
            <li className="nav-item w-50">
              <button
                className={`nav-link w-100 ${
                  activeTab === "login" ? "active" : ""
                }`}
                onClick={() => handleTabSwitch("login")}
              >
                Login
              </button>
            </li>
            <li className="nav-item w-50">
              <button
                className={`nav-link w-100 ${
                  activeTab === "cadastro" ? "active" : ""
                }`}
                onClick={() => handleTabSwitch("cadastro")}
              >
                Cadastro
              </button>
            </li>
          </ul>

          <div key={activeTab} className="fade-in">
            {activeTab === "login" ? (
              <form onSubmit={handleLogin}>
                <div className="mb-3">
                  <label className="form-label">Email</label>
                  <input
                    type="email"
                    className={`form-control ${errors.loginEmail ? "is-invalid" : ""}`}
                    placeholder="seu@email.com"
                    value={loginEmail}
                    onChange={(e) => {
                      setLoginEmail(e.target.value);
                      if (errors.loginEmail)
                        setErrors({ ...errors, loginEmail: "" });
                    }}
                  />
                  {errors.loginEmail && (
                    <div className="invalid-feedback">{errors.loginEmail}</div>
                  )}
                </div>

                <div className="mb-3">
                  <label className="form-label">Senha</label>
                  <input
                    type="password"
                    className={`form-control ${errors.loginPassword ? "is-invalid" : ""}`}
                    placeholder="*******"
                    value={loginPassword}
                    onChange={(e) => {
                      setLoginPassword(e.target.value);
                      if (errors.loginPassword)
                        setErrors({ ...errors, loginPassword: "" });
                    }}
                  />
                  {errors.loginPassword && (
                    <div className="invalid-feedback">
                      {errors.loginPassword}
                    </div>
                  )}
                </div>

                <button type="submit" className="btn btn-primary w-100">
                  Entrar
                </button>
              </form>
            ) : (
              <form onSubmit={handleCadastro}>
                <div className="mb-3">
                  <label className="form-label">Nome</label>
                  <input
                    type="text"
                    className={`form-control ${errors.regNome ? "is-invalid" : ""}`}
                    placeholder="João"
                    value={regNome}
                    onChange={(e) => {
                      setRegNome(e.target.value);
                      if (errors.regNome) setErrors({ ...errors, regNome: "" });
                    }}
                  />
                  {errors.regNome && (
                    <div className="invalid-feedback">{errors.regNome}</div>
                  )}
                </div>

                <div className="mb-3">
                  <label className="form-label">Email</label>
                  <input
                    type="email"
                    className={`form-control ${errors.regEmail ? "is-invalid" : ""}`}
                    placeholder="seu@email.com"
                    value={regEmail}
                    onChange={(e) => {
                      setRegEmail(e.target.value);
                      if (errors.regEmail)
                        setErrors({ ...errors, regEmail: "" });
                    }}
                  />
                  {errors.regEmail && (
                    <div className="invalid-feedback">{errors.regEmail}</div>
                  )}
                </div>

                <div className="mb-3">
                  <label className="form-label">Senha</label>
                  <input
                    type="password"
                    className={`form-control ${errors.regPassword ? "is-invalid" : ""}`}
                    placeholder="*******"
                    value={regPassword}
                    onChange={(e) => {
                      setRegPassword(e.target.value);
                      if (errors.regPassword)
                        setErrors({ ...errors, regPassword: "" });
                    }}
                  />
                  {errors.regPassword && (
                    <div className="invalid-feedback">{errors.regPassword}</div>
                  )}
                </div>

                <div className="form-check mb-3">
                  <input
                    type="checkbox"
                    className={`form-check-input ${errors.regConsentimento ? "is-invalid" : ""}`}
                    id="consentimento"
                    checked={regConsentimento}
                    onChange={(e) => {
                      setRegConsentimento(e.target.checked);
                      if (errors.regConsentimento)
                        setErrors({ ...errors, regConsentimento: "" });
                    }}
                  />
                  <label className="form-check-label" htmlFor="consentimento">
                    Aceito o{" "}
                    <Link
                      to={ROUTES.TERMS}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      termo de consentimento
                    </Link>
                  </label>
                  {errors.regConsentimento && (
                    <div className="invalid-feedback">
                      {errors.regConsentimento}
                    </div>
                  )}
                </div>

                <button type="submit" className="btn btn-success w-100">
                  Cadastrar
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
