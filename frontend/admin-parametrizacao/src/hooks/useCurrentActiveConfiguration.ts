import { useQuery } from "@tanstack/react-query";
import configurationsService from "../services/configurationsService";

export const CURRENT_CONFIGURATION_KEY = "currentConfiguration";

const useCurrentActiveConfiguration = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: [CURRENT_CONFIGURATION_KEY],
    queryFn: configurationsService.getCurrentActiveConfig,
  });

  return {
    currentConfiguration: data,
    isLoading,
    error,
  };
};

export default useCurrentActiveConfiguration;
