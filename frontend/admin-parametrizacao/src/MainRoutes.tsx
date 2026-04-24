import { Routes, Route, Navigate } from "react-router";

import { ROUTES } from "./utils/routes";
import Login from "./pages/Login";
import Home from "./pages/Home";
import MainLayout from "./pages/MainLayout";
import ProtectedRoute from "./pages/ProtectedRoute";

const MainRoutes = () => {
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<Login />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Navigate to={ROUTES.HOME} replace />} />
        <Route element={<MainLayout />}>
          <Route path={ROUTES.HOME} element={<Home />} />
        </Route>
      </Route>
    </Routes>
  );
};

export default MainRoutes;
