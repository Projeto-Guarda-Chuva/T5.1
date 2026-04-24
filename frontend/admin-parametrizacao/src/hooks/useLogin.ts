import { useMutation } from "@tanstack/react-query";

import authService from "../services/auth";
import type { LoginEntry, User } from "../types/users";

const useLogin = () => {
  const mutation = useMutation<User | null, Error, LoginEntry>({
    mutationFn: authService.login,
  });

  return {
    ...mutation,
    login: mutation.mutateAsync,
  };
};

export default useLogin;
