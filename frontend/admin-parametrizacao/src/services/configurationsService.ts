import api from "../api";
import type { Configuration, ConfigurationResponse, CreateConfigurationPayload, CurrentConfigurationResponse } from "../types/configurations";

const baseUrl = "/configurations";

const getConfigurations = async (): Promise<ConfigurationResponse | undefined> => {
  const response = await api.get(baseUrl);

  return response.data;
};

const getConfigurationsDetails = async (id: string): Promise<Configuration | undefined> => {
  const response = await api.get(`${baseUrl}/${id}`);

  return response.data;
};

const createConfiguration = async (obj: CreateConfigurationPayload): Promise<Configuration> => {
  const response = await api.post(baseUrl, obj);

  return response.data;
};

const getCurrentActiveConfig = async (): Promise<CurrentConfigurationResponse | undefined> => {
  const response = await api.get(`${baseUrl}/current`);

  return response.data;
};

const activateConfiguration = async (id: string): Promise<Configuration> => {
  const response = await api.patch(`${baseUrl}/${id}/activate`);
  return response.data;
};

export default { getConfigurations, getConfigurationsDetails, createConfiguration, getCurrentActiveConfig, activateConfiguration };
