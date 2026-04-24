import { Routes, Route } from "react-router-dom";
import { ROUTES } from "./utils/routes";
import Login from "./pages/Login/index";
import Home from "./pages/Home/index";
import About from "./pages/About/index";

const MainRoutes = () => {
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<Login />} />
      <Route path={ROUTES.HOME} element={<Home />} />
      <Route path={ROUTES.ABOUT} element={<About />} />
    </Routes>
  );
};

export default MainRoutes;
