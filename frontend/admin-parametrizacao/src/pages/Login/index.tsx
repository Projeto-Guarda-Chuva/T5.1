import styles from "./styles.module.css";
import LoginForm from "../../components/LoginForm";

const Login = () => {
  return (
    <div
      className={`${styles.loginPageBg} d-flex align-items-center justify-content-center vh-100`}
    >
      <main className={styles.loginContainer}>
        <div className={`card border-0 ${styles.loginCard}`}>
          <div className="card-body p-4 p-sm-5">
            <div className="text-center mb-4">
              <i
                className={`bi bi-droplet-half d-block mb-3 ${styles.logoIcon}`}
              ></i>
              <h2 className="fw-bold mb-1">Parametrização Admin</h2>
              <p className="text-muted small">
                Controle de parâmetros da Água-viva
              </p>
            </div>

            <LoginForm onSubmit={() => {}} />
          </div>
        </div>

        {/* Rodapé opcional */}
        <div className="text-center mt-4">
          <p className="text-muted small mb-0">&copy; 2026 ODS CORP</p>
        </div>
      </main>
    </div>
  );
};

export default Login;
