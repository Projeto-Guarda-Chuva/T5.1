import { ROUTES } from "../../utils/routes";

export interface NavItem {
  label: string;
  path: string;
  matchPath: string;
}

export const navItems: NavItem[] = [
  {
    label: "Dashboard",
    matchPath: ROUTES.HOME,
    path: ROUTES.HOME,
  },
  {
    label: "Parâmetros",
    matchPath: ROUTES.PARAMETERS,
    path: ROUTES.PARAMETERS,
  },
  {
    label: "Histórico de Vídeos",
    matchPath: ROUTES.VIDEOS_HISTORY,
    path: ROUTES.VIDEOS_HISTORY,
  },
];
