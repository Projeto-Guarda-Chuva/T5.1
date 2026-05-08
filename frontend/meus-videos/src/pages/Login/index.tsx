import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ROUTES } from "../../utils/routes";
import { FaGoogle } from "react-icons/fa";

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

  useEffect(() => {
    // Inicializa dados mockados para facilitar os testes de diferentes cenários
    const users = localStorage.getItem("mock_users");
    if (!users) {
      const initialUsers = [
        { nome: "Com Vídeos", email: "comvideos@teste.com", password: "123" },
        { nome: "Sem Vídeos", email: "semvideos@teste.com", password: "123" },
      ];
      localStorage.setItem("mock_users", JSON.stringify(initialUsers));

      const mockVideos = [
        {
          id: "1",
          date: "28 Abr 2026 às 14:30",
          thumbnail: "https://picsum.photos/seed/vid1/1280/720",
          src: "https://www.w3schools.com/html/mov_bbb.mp4",
        },
        {
          id: "2",
          date: "25 Abr 2026 às 09:15",
          thumbnail: "https://picsum.photos/seed/vid2/640/360",
          src: "https://www.w3schools.com/html/movie.mp4",
        },
        {
          id: "3",
          date: "20 Abr 2026 às 18:45",
          thumbnail: "https://picsum.photos/seed/vid3/640/360",
          src: "https://www.w3schools.com/html/mov_bbb.mp4",
        },
        {
          id: "4",
          date: "15 Abr 2026 às 10:00",
          thumbnail: "https://picsum.photos/seed/vid4/640/360",
          src: "https://www.w3schools.com/html/movie.mp4",
        },
      ];
      localStorage.setItem(
        "videos_comvideos@teste.com",
        JSON.stringify(mockVideos),
      );
      localStorage.setItem("videos_semvideos@teste.com", JSON.stringify([]));
    }
  }, []);

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

    if (Object.keys(newErrors).length === 0) {
      // Simulando o login com dados salvos no localStorage
      const users = JSON.parse(localStorage.getItem("mock_users") || "[]");
      const user = users.find(
        (u: any) => u.email === loginEmail && u.password === loginPassword,
      );

      if (user) {
        alert(`Bem-vindo(a), ${user.nome}!`);
        localStorage.setItem("logged_user", JSON.stringify(user));
        navigate(ROUTES.HOME); // Redireciona para a página "Sobre" após o login mockado
      } else {
        setErrors({ loginPassword: "E-mail ou senha incorretos." });
      }
    }
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

    if (Object.keys(newErrors).length === 0) {
      // Simulando o cadastro salvando os dados no localStorage
      const users = JSON.parse(localStorage.getItem("mock_users") || "[]");

      if (users.find((u: any) => u.email === regEmail)) {
        setErrors({ regEmail: "Este e-mail já está em uso." });
        return;
      }

      const newUser = { nome: regNome, email: regEmail, password: regPassword };
      users.push(newUser);
      localStorage.setItem("mock_users", JSON.stringify(users));
      // Certifica que o usuário novo comece com o estado de vídeos vazio
      localStorage.setItem(`videos_${regEmail}`, JSON.stringify([]));

      alert("Cadastro realizado com sucesso! Por favor, faça login.");
      setLoginEmail(regEmail); // Preenche o e-mail no login
      setLoginPassword(""); // Limpa o campo de senha no login
      setActiveTab("login"); // Troca para a aba de login
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

                  <button type="submit" className="btn btn-primary w-100">
                    Entrar
                  </button>
                </form>

                <div className="d-flex align-items-center my-3">
                  <hr className="flex-grow-1 text-muted" />
                  <span className="mx-3 text-muted small">ou</span>
                  <hr className="flex-grow-1 text-muted" />
                </div>

                <button
                  type="button"
                  className="btn btn-outline-danger w-100 d-flex align-items-center justify-content-center gap-2"
                >
                  <FaGoogle size={18} />
                  Entrar com o Google
                </button>
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

                  <button type="submit" className="btn btn-success w-100">
                    Cadastrar
                  </button>
                </form>

                <div className="d-flex align-items-center my-3">
                  <hr className="flex-grow-1 text-muted" />
                  <span className="mx-3 text-muted small">ou</span>
                  <hr className="flex-grow-1 text-muted" />
                </div>

                <button
                  type="button"
                  className="btn btn-outline-danger w-100 d-flex align-items-center justify-content-center gap-2"
                >
                  <FaGoogle size={18} />
                  Cadastrar com o Google
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
