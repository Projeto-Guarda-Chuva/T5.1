import { useQuery } from "@tanstack/react-query";

import operationLogsService from "../services/operationLogsService";

const useOperationLog = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ["operationLogs"],
    queryFn: operationLogsService.getOperationLogs,
    refetchInterval: 60 * 1000,
  });

  return {
    operationLogs: data,
    isLoading,
    error,
  };
};

export default useOperationLog;
