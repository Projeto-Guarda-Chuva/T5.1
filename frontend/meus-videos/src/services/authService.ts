import api from "../api";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
}

export interface GoogleLoginRequest {
  credential: string;
}

export interface GoogleLoginResponse extends TokenResponse {
  token_type: string;
  participant_id: string;
  email: string;
  nome: string;
  is_new_user: boolean;
}

export interface RegisterRequest {
  nome: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  participant_id: string;
  email: string;
  nome: string;
  message: string;
}

const login = async (credentials: LoginRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>("/auth/login", credentials);
  return response.data;
};

const loginWithGoogle = async (
  payload: GoogleLoginRequest,
): Promise<GoogleLoginResponse> => {
  const response = await api.post<GoogleLoginResponse>("/auth/google", payload);
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
  loginWithGoogle,
  register,
};
