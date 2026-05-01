import { NavLink } from "react-router";
import styles from "./styles.module.css";

import { navItems } from "./navItems";

const Navbar = () => {
  return (
    <nav className={`navbar navbar-expand-lg navbar-dark bg-primary ${styles.customNavbar}`}>
      <div className="container">
        <a className="navbar-brand fw-bold d-flex align-items-center" href="#">
          <i className="bi bi-droplet-half me-2"></i>
          Admin Parametrização
        </a>

        <button className="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbarAdmin">
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarAdmin">
          <ul className="navbar-nav ms-auto mb-2 mb-lg-0">
            {navItems.map((item) => (
              <li key={item.label} className="nav-item">
                <NavLink to={item.path} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
                  {item.label}
                </NavLink>
              </li>
            ))}

            <li className="mt-2 mt-lg-0 ms-lg-3">
              <button className="btn btn-sm btn-outline-light w-100 text-white">Sair</button>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
