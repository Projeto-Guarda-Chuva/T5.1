import axios from "axios";
import type { AxiosResponse, AxiosError } from "axios";

import authStorage from "./utils/authStorage";
import { ROUTES } from "./utils/routes";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

api.interceptors.request.use(
  (config) => {
    const token = authStorage.getToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response: AxiosResponse) => response,

  (error: AxiosError) => {
    const status = error.response?.status;

    if (status === 401) {
      authStorage.removeToken();

      window.location.href = ROUTES.LOGIN;
    }

    return Promise.reject(error);
  },
);

export default api;
