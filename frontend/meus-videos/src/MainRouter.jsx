import { Routes, Route } from "react-router-dom";
import { ROUTES } from "./utils/routes";
import Login from "./pages/Login/index";
import About from "./pages/About/index";
import Terms from "./pages/Terms/index";
import Home from "./pages/Home/index";
import StatusGravacao from "./pages/StatusGravacao/index";

const MainRoutes = () => {
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<Login />} />
      <Route path={ROUTES.ABOUT} element={<About />} />
      <Route path={ROUTES.TERMS} element={<Terms />} />
      <Route path={ROUTES.HOME} element={<Home />} />
      <Route path={ROUTES.STATUS_GRAVACAO} element={<StatusGravacao />} />
    </Routes>
  );
};

export default MainRoutes;