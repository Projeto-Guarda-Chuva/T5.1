import { useMutation } from "@tanstack/react-query";

import authService from "../services/auth";
import type { LoginEntry, LoginResponse } from "../types/users";

const useLogin = () => {
  const mutation = useMutation<LoginResponse | null, Error, LoginEntry>({
    mutationFn: authService.login,
  });

  return {
    ...mutation,
    login: mutation.mutateAsync,
  };
};

export default useLogin;
