import { useState } from "react";

import styles from "./styles.module.css";
import type { LoginEntry } from "../../types/users";

type LoginFormProps = {
  onSubmit: (data: LoginEntry) => void;
  loading: boolean;
  error: string | undefined;
};

const LoginForm = ({ onSubmit, error, loading }: LoginFormProps) => {
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const handleSubmit = (e: React.SyntheticEvent) => {
    e.preventDefault();

    onSubmit({ username, password });
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <div className="alert alert-danger py-2 small d-flex align-items-center" role="alert">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          {error}
        </div>
      )}

      <div className="form-floating mb-3">
        <input
          type="text"
          className={`form-control ${styles.customRounded} ${error ? "is-invalid" : ""}`}
          id="adminUser"
          placeholder="nomeusuario"
          required
          value={username}
          onChange={({ target }) => setUsername(target.value)}
          disabled={loading}
        />
        <label htmlFor="adminUser">Usuário</label>
      </div>

      <div className="form-floating mb-3">
        <input
          type="password"
          className={`form-control ${styles.customRounded} ${error ? "is-invalid" : ""}`}
          id="adminPassword"
          placeholder="Senha"
          required
          value={password}
          onChange={({ target }) => setPassword(target.value)}
          disabled={loading}
        />
        <label htmlFor="adminPassword">Senha</label>
      </div>

      <div className="d-flex justify-content-between align-items-center mb-4 small">
        <div className="form-check">
          <input className="form-check-input" type="checkbox" id="rememberMe" disabled={loading} />
          <label className="form-check-label text-muted" htmlFor="rememberMe">
            Lembrar-me
          </label>
        </div>
        <a href="#" className="text-primary text-decoration-none fw-semibold">
          Esqueceu a senha?
        </a>
      </div>

      <button className={`btn btn-primary w-100 py-3 ${styles.btnLogin}`} type="submit" disabled={loading}>
        {loading ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
            <span role="status">Acessando...</span>
          </>
        ) : (
          <>
            <i className="bi bi-box-arrow-in-right me-2"></i>Acessar Painel
          </>
        )}
      </button>
    </form>
  );
};

export default LoginForm;
