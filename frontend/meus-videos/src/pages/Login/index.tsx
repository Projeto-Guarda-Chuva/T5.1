import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ROUTES } from "../../utils/routes";
import {
  GoogleOAuthProvider,
  GoogleLogin,
  CredentialResponse,
} from "@react-oauth/google";
import { jwtDecode } from "jwt-decode";
import authService from "../../services/authService";
import participantesService from "../../services/participantesService";

interface GoogleDecodedToken {
  name: string;
  email: string;
}

export default function AuthPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"login" | "cadastro">("login");

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const [regNome, setRegNome] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConsentimento, setRegConsentimento] = useState(false);

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleTabSwitch = (tab: "login" | "cadastro") => {
    setActiveTab(tab);
    setErrors({});
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    if (!loginEmail) newErrors.loginEmail = "O e-mail é obrigatório.";
    if (!loginPassword) newErrors.loginPassword = "A senha é obrigatória.";
    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      try {
        setLoading(true);
        const response = await authService.login({
          email: loginEmail,
          password: loginPassword,
        });

        localStorage.setItem("access_token", response.access_token);
        localStorage.setItem(
          "logged_user",
          JSON.stringify({ email: loginEmail }),
        );
        alert("Login realizado com sucesso!");
        navigate(ROUTES.HOME);
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.detail || "E-mail ou senha incorretos.";
        setErrors({ loginPassword: errorMessage });
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCadastro = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    if (!regNome) newErrors.regNome = "O nome é obrigatório.";
    if (!regEmail) newErrors.regEmail = "O e-mail é obrigatório.";
    if (!regPassword) newErrors.regPassword = "A senha é obrigatória.";
    if (!regConsentimento)
      newErrors.regConsentimento =
        "Você deve aceitar o termo de consentimento.";
    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      try {
        setLoading(true);

        // Primeiro registra o participante
        const registerResponse = await authService.register({
          nome: regNome,
          email: regEmail,
          password: regPassword,
        });

        // Logo após cadastrar, fazemos o login automaticamente para obter o token (JWT) desse novo usuário!
        const loginResponse = await authService.login({
          email: regEmail,
          password: regPassword,
        });

        // Salva o token da nova conta no localStorage (sobrescrevendo qualquer token antigo)
        localStorage.setItem("access_token", loginResponse.access_token);

        // Depois aceita o termo
        if (regConsentimento) {
          await participantesService.aceitarTermo(registerResponse.participant_id, {
            aceitou: true,
            versao_termo: "v1.0",
          });
        }

        localStorage.setItem(
          "logged_user",
          JSON.stringify({
            email: regEmail,
            nome: regNome,
            participantId: registerResponse.participant_id,
          }),
        );
        alert("Cadastro realizado com sucesso!");
        navigate("/status-gravacao");
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.detail ||
          "Erro ao realizar cadastro. Tente novamente.";
        setErrors({ regEmail: errorMessage });
      } finally {
        setLoading(false);
      }
    }
  };

  const handleGoogleLogin = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      setErrors({
        ...errors,
        google: "Login com Google falhou. Tente novamente.",
      });
      return;
    }

    try {
      const decoded: GoogleDecodedToken = jwtDecode(
        credentialResponse.credential,
      );
      const { name, email } = decoded;

      // Aqui você poderia fazer uma chamada ao backend para registrar o usuário do Google
      // Por enquanto, vamos apenas fazer login local
      localStorage.setItem(
        "logged_user",
        JSON.stringify({ email, nome: name }),
      );
      alert(`Bem-vindo(a), ${name}!`);
      navigate(ROUTES.HOME);
    } catch (error) {
      setErrors({
        ...errors,
        google: "Falha no login com Google. Tente novamente.",
      });
    }
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
              <>
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
                      <div className="invalid-feedback">
                        {errors.loginEmail}
                      </div>
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

                  <button
                    type="submit"
                    className="btn btn-primary w-100"
                    disabled={loading}
                  >
                    {loading ? "Entrando..." : "Entrar"}
                  </button>
                </form>
              </>
            ) : (
              <>
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
                        if (errors.regNome)
                          setErrors({ ...errors, regNome: "" });
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
                      <div className="invalid-feedback">
                        {errors.regPassword}
                      </div>
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

                  <button
                    type="submit"
                    className="btn btn-success w-100"
                    disabled={loading}
                  >
                    {loading ? "Cadastrando..." : "Cadastrar"}
                  </button>
                </form>
              </>
            )}

            <div className="d-flex align-items-center my-3">
              <hr className="flex-grow-1 text-muted" />
              <span className="mx-3 text-muted small">ou</span>
              <hr className="flex-grow-1 text-muted" />
            </div>

            <div className="d-flex justify-content-center">
              <GoogleOAuthProvider
                clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ""}
              >
                <GoogleLogin
                  onSuccess={handleGoogleLogin}
                  onError={() => {
                    setErrors({
                      ...errors,
                      google: "Falha no login com Google. Tente novamente.",
                    });
                  }}
                  useOneTap
                />
              </GoogleOAuthProvider>
            </div>
            {errors.google && (
              <div className="text-danger text-center mt-2 small">
                {errors.google}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
