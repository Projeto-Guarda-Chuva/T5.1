import { Link } from "react-router-dom";
import { ROUTES } from "../../utils/routes";
import { FaGithub, FaTwitter, FaInstagram } from "react-icons/fa";

export default function Footer() {
  return (
    <footer className="bg-white py-4 mt-auto border-top">
      <div className="container d-flex flex-column flex-md-row justify-content-between align-items-center">
        <div className="text-muted small mb-3 mb-md-0 text-center text-md-start">
          © {new Date().getFullYear()} Projeto Guarda Chuva. Todos os direitos
          reservados.
        </div>

        <div className="d-flex gap-3 mb-3 mb-md-0">
          <Link
            to={ROUTES.TERMS}
            className="text-decoration-none text-muted small"
          >
            Termos de Uso
          </Link>
        </div>
      </div>
    </footer>
  );
}
