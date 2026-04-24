import { Navigate, Outlet } from "react-router";
import authStorage from "../../utils/authStorage";
import { ROUTES } from "../../utils/routes";

const ProtectedRoute = () => {
  const isAuthenticated = authStorage.getToken();

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
