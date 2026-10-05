import { apiFetch } from './client';

export interface UserProgress {
  userId: string;
  lessonsStarted: number;
  lessonsCompleted: number;
  studyMinutes: number;
  lastActivityAt: string | null;
  updatedAt: string | null;
}

export function getMyProgress(): Promise<UserProgress> {
  return apiFetch<UserProgress>('/progress/me');
}
