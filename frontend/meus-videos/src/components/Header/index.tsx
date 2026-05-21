import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ROUTES } from "../../utils/routes";
import { FaPlayCircle } from "react-icons/fa";

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const isLoggedIn = !!localStorage.getItem("logged_user");

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("logged_user");
    setIsMenuOpen(false);
  };

  return (
    <header>
      <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div className="container">
          <Link
            className="navbar-brand fw-bold text-primary d-flex align-items-center gap-2"
            to={isLoggedIn ? ROUTES.HOME : ROUTES.LOGIN}
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
              {isLoggedIn && (
                <li className="nav-item">
                  <Link
                    className="nav-link"
                    to={ROUTES.HOME}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Menu
                  </Link>
                </li>
              )}
              <li className="nav-item">
                <Link
                  className="nav-link"
                  to={ROUTES.ABOUT}
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sobre
                </Link>
              </li>
              {isLoggedIn ? (
                <li className="nav-item">
                  <Link
                    className="nav-link text-danger"
                    to={ROUTES.LOGIN}
                    onClick={handleLogout}
                  >
                    Sair
                  </Link>
                </li>
              ) : (
                <li className="nav-item">
                  <Link
                    className="nav-link text-primary"
                    to={ROUTES.LOGIN}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Entrar
                  </Link>
                </li>
              )}
            </ul>
          </div>
        </div>
      </nav>
    </header>
  );
}
