import apiClient from './client';

export interface WorkerStats {
  total_points: number;
  tasks_completed: number;
  current_streak: number;
  longest_streak: number;
  last_task_completed_at: string | null;
  level: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  total_points: number;
  tasks_completed: number;
  current_streak: number;
}

export async function getWorkerStats(): Promise<{ data: WorkerStats }> {
  return apiClient.get('/mobile/gamification/stats');
}

export async function getLeaderboard(): Promise<{ data: LeaderboardEntry[] }> {
  return apiClient.get('/mobile/gamification/leaderboard');
}
