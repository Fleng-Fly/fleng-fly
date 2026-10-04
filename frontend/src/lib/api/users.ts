import { apiFetch } from './client';

export interface CurrentUser {
  id: string;
  email: string;
  displayName: string;
  level: number;
  xp: number;
  createdAt: string;
}

export function getCurrentUser(): Promise<CurrentUser> {
  return apiFetch<CurrentUser>('/users/me');
}
