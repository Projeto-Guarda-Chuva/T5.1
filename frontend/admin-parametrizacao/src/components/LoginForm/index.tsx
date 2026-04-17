import { useState } from "react";

import styles from "./styles.module.css";

type LoginFormProps = {
  onSubmit: (data: { userName: string; password: string }) => void;
};

const LoginForm = ({ onSubmit }: LoginFormProps) => {
  const [userName, setUserName] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const handleSubmit = (e: React.SyntheticEvent) => {
    e.preventDefault();

    onSubmit({ userName, password });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-floating mb-3">
        <input
          type="text"
          className={`form-control ${styles.customRounded}`}
          id="adminUser"
          placeholder="nomeusuario"
          required
          value={userName}
          onChange={({ target }) => setUserName(target.value)}
        />
        <label htmlFor="adminUser">Usuário</label>
      </div>

      <div className="form-floating mb-3">
        <input
          type="password"
          className={`form-control ${styles.customRounded}`}
          id="adminPassword"
          placeholder="Senha"
          required
          value={password}
          onChange={({ target }) => setPassword(target.value)}
        />
        <label htmlFor="adminPassword">Senha</label>
      </div>

      <div className="d-flex justify-content-between align-items-center mb-4 small">
        <div className="form-check">
          <input className="form-check-input" type="checkbox" id="rememberMe" />
          <label className="form-check-label text-muted" htmlFor="rememberMe">
            Lembrar-me
          </label>
        </div>
        <a href="#" className="text-primary text-decoration-none fw-semibold">
          Esqueceu a senha?
        </a>
      </div>

      <button
        className={`btn btn-primary w-100 py-3 ${styles.btnLogin}`}
        type="submit"
      >
        <i className="bi bi-box-arrow-in-right me-2"></i>Acessar Painel
      </button>
    </form>
  );
};

export default LoginForm;
