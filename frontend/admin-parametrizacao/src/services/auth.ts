import type { LoginEntry, User } from "../types/users";

import api from "../api";

const login = async (obj: LoginEntry): Promise<User | null> => {
  const response = await api.get<User[]>("/users", {
    params: {
      username: obj.username,
      password: obj.password,
    },
  });

  return response.data[0] ?? null;
};

export default {
  login,
};
