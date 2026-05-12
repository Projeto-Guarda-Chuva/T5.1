import { useMutation, type UseMutationOptions } from "@tanstack/react-query";

import configurationsService from "../services/configurationsService";
import type { Configuration } from "../types/configurations";

const useActivateConfiguration = (options?: UseMutationOptions<Configuration, Error, string>) => {
  const mutation = useMutation<Configuration, Error, string>({
    mutationFn: configurationsService.activateConfiguration,
    ...options,
  });

  return {
    activateConfiguration: mutation.mutateAsync,
    ...mutation,
  };
};

export default useActivateConfiguration;
