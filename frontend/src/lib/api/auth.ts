import { apiFetch } from './client';
import type { CurrentUser } from './users';

export interface AuthResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  user: CurrentUser;
}

export interface RegisterInput {
  email: string;
  password: string;
  displayName: string;
}

/** Create an account and establish a session (sets the refresh cookie). */
export function register(input: RegisterInput): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/** Authenticate and establish a session (sets the refresh cookie). */
export function login(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

/** Revoke the current session and clear the refresh cookie. */
export function logout(): Promise<void> {
  return apiFetch<void>(
    '/auth/logout',
    { method: 'POST' },
    { retryOnUnauthorized: false },
  );
}
