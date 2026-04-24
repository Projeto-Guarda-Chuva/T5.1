import { Outlet } from "react-router";
import Navbar from "../../components/Navbar";

import styles from "./styles.module.css";

const MainLayout = () => {
  return (
    <div className={styles.pageBg}>
      <Navbar />

      <main className="container mt-4">
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
