import { apiFetch } from './client';

export interface Health {
  status: string;
  service: string;
  timestamp: string;
  database: 'up' | 'down';
}

export function getHealth(): Promise<Health> {
  return apiFetch<Health>('/health');
}
