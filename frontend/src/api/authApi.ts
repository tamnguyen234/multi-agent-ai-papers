import client from './client';

export interface UserRegisterPayload {
  username: string;
  password: string;
  full_name: string;
  email: string;
}

export interface UserLoginPayload {
  username: string;
  password: string;
}

export interface UserResponse {
  id: number;
  username: string;
  full_name: string;
  email: string;
  noti_daily: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export const authApi = {
  register: async (payload: UserRegisterPayload): Promise<UserResponse> => {
    const response = await client.post<UserResponse>('/auth/register', payload);
    return response.data;
  },

  login: async (payload: UserLoginPayload): Promise<TokenResponse> => {
    const response = await client.post<TokenResponse>('/auth/login', payload);
    return response.data;
  },

  getMe: async (): Promise<UserResponse> => {
    const response = await client.get<UserResponse>('/auth/me');
    return response.data;
  },
};
