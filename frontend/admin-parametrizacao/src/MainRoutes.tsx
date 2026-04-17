import { Routes, Route } from "react-router";

import { ROUTES } from "./utils/routes";
import Login from "./pages/Login";
import Home from "./pages/Home";

const MainRoutes = () => {
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<Login />} />
      <Route path={ROUTES.HOME} element={<Home />} />
    </Routes>
  );
};

export default MainRoutes;
