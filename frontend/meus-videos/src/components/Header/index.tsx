import { useState } from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "../../utils/routes";
import { FaPlayCircle } from "react-icons/fa";

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header>
      <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div className="container">
          <Link
            className="navbar-brand fw-bold text-primary d-flex align-items-center gap-2"
            to={ROUTES.LOGIN}
          >
            <FaPlayCircle size={24} />
            Meus Vídeos
          </Link>

          <button
            className="navbar-toggler"
            type="button"
            onClick={toggleMenu}
            aria-expanded={isMenuOpen}
            aria-label="Alternar navegação"
          >
            <span className="navbar-toggler-icon"></span>
          </button>

          <div
            className={`collapse navbar-collapse ${isMenuOpen ? "show" : ""}`}
          >
            <ul className="navbar-nav ms-auto">
              <li className="nav-item">
                <Link
                  className="nav-link"
                  to={ROUTES.ABOUT}
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sobre
                </Link>
              </li>
              <li className="nav-item">
                <Link
                  className="nav-link text-danger"
                  to={ROUTES.LOGIN}
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sair
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </header>
  );
}
