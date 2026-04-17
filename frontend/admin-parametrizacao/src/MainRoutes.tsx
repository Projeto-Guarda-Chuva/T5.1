import { Routes, Route } from "react-router";

import { ROUTES } from "./utils/routes";
import Login from "./pages/Login";

const MainRoutes = () => {
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<Login />} />
    </Routes>
  );
};

export default MainRoutes;
