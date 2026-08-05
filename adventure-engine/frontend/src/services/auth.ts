import { apiGet, apiPost } from './api';

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserRead {
  id: number;
  email: string;
  created_at: string;
}

export function register(email: string, password: string): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/register', { email, password });
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/login', { email, password });
}

export function getMe(token: string): Promise<UserRead> {
  return apiGet<UserRead>('/auth/me', undefined, token);
}
