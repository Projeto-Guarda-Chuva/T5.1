import styles from "./styles.module.css";
import LoginForm from "../../components/LoginForm";
import useLogin from "../../hooks/useLogin";
import type { LoginEntry } from "../../types/users";
import { useState } from "react";
import { useNavigate } from "react-router";
import { ROUTES } from "../../utils/routes";
import authStorage from "../../utils/authStorage";

const Login = () => {
  const { login, isPending } = useLogin();

  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  const handleSubmitLogin = async (loginEntry: LoginEntry) => {
    setError(null);

    try {
      const user = await login(loginEntry);

      if (!user) {
        setError("Erro ao fazer login");
        return;
      }

      authStorage.setToken(user.token);

      navigate(ROUTES.HOME);
    } catch (err) {
      setError("Erro de conexão tente novamente");

      console.error(err);
    }
  };

  return (
    <div className={`${styles.loginPageBg} d-flex align-items-center justify-content-center vh-100`}>
      <main className={styles.loginContainer}>
        <div className={`card border-0 ${styles.loginCard}`}>
          <div className="card-body p-4 p-sm-5">
            <div className="text-center mb-4">
              <i className={`bi bi-droplet-half d-block mb-3 ${styles.logoIcon}`}></i>
              <h2 className="fw-bold mb-1">Parametrização Admin</h2>
              <p className="text-muted small">Controle de parâmetros da Água-viva</p>
            </div>

            <LoginForm onSubmit={handleSubmitLogin} loading={isPending} error={error ?? undefined} />
          </div>
        </div>

        <div className="text-center mt-4">
          <p className="text-muted small mb-0">&copy; 2026 ODS CORP</p>
        </div>
      </main>
    </div>
  );
};

export default Login;
