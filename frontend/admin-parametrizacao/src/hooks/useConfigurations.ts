import { useQuery } from "@tanstack/react-query";
import configurationsService from "../services/configurationsService";

export const CONFIGURATIONS_KEY = "configurations";

const useConfigurations = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: [CONFIGURATIONS_KEY],
    queryFn: configurationsService.getConfigurations,
    refetchInterval: 600 * 1000,
  });

  return {
    configurations: data,
    isLoading,
    error,
  };
};

export default useConfigurations;
