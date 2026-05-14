import { useQuery } from "@tanstack/react-query";

import configurationsService from "../services/configurationsService";

const useDetailsConfigurations = (id) => {
  const { data, isLoading, error } = useQuery({
    queryKey: [`configuration`, id],
    queryFn: () => configurationsService.getConfigurationsDetails(id),
    refetchOnWindowFocus: false,
    enabled: !!id,
  });

  return {
    configurationDetail: data,
    isLoading,
    error,
  };
};

export default useDetailsConfigurations;
