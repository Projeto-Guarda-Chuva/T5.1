import api from "../api";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
}

export interface RegisterRequest {
  nome: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  email: string;
  nome: string;
  message: string;
}

const login = async (credentials: LoginRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>("/auth/login", credentials);
  return response.data;
};

const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
  const response = await api.post<RegisterResponse>(
    "/auth/register-participante",
    data,
  );
  return response.data;
};

export default {
  login,
  register,
};
