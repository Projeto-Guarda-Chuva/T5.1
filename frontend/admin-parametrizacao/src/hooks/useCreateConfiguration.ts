import { useMutation, type UseMutationOptions } from "@tanstack/react-query";

import configurationsService from "../services/configurationsService";
import type { Configuration, CreateConfigurationPayload } from "../types/configurations";

const useCreateConfiguration = (options?: UseMutationOptions<Configuration, Error, CreateConfigurationPayload>) => {
  const mutation = useMutation<Configuration, Error, CreateConfigurationPayload>({
    mutationFn: configurationsService.createConfiguration,
    ...options,
  });

  return {
    createConfiguration: mutation.mutateAsync,
    ...mutation,
  };
};

export default useCreateConfiguration;
