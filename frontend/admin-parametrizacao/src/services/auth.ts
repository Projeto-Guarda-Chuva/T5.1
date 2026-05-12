import type { LoginEntry, LoginResponse } from "../types/users";

import api from "../api";

const login = async (obj: LoginEntry): Promise<LoginResponse | null> => {
  const response = await api.post<LoginResponse>("/auth/login", obj);

  return response.data ?? null;
};

export default {
  login,
};
