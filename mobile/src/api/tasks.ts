import apiClient from './client';

export interface PickTask {
  id: string;
  transaction_id: string;
  transaction_type: string;
  reference_number: string;
  sku_code: string;
  sku_name: string;
  source_entity_type: string;
  source_entity_code: string;
  quantity: string;
  batch_number: string;
  task_status: string;
  assigned_to_name: string | null;
  assigned_at: string | null;
  task_started_at: string | null;
  task_completed_at: string | null;
  points_awarded: number;
  created_at: string;
}

export interface DropTask {
  id: string;
  transaction_id: string;
  transaction_type: string;
  reference_number: string;
  sku_code: string;
  sku_name: string;
  dest_entity_type: string;
  dest_entity_code: string;
  quantity: string;
  batch_number: string;
  task_status: string;
  assigned_to_name: string | null;
  assigned_at: string | null;
  task_started_at: string | null;
  task_completed_at: string | null;
  points_awarded: number;
  paired_pick_id: string | null;
  created_at: string;
}

export interface AvailableTasksData {
  picks: PickTask[];
  drops: DropTask[];
}

export async function getAvailableTasks(): Promise<{ data: AvailableTasksData }> {
  return apiClient.get('/mobile/tasks/available');
}

export async function claimPickTask(pickId: string): Promise<{ data: PickTask }> {
  return apiClient.post(`/mobile/tasks/picks/${pickId}/claim`);
}

export async function claimDropTask(dropId: string): Promise<{ data: DropTask }> {
  return apiClient.post(`/mobile/tasks/drops/${dropId}/claim`);
}

export async function startPickTask(pickId: string): Promise<{ data: PickTask }> {
  return apiClient.post(`/mobile/tasks/picks/${pickId}/start`);
}

export async function completePickTask(
  pickId: string
): Promise<{ data: { pick: PickTask; drop: DropTask | null } }> {
  return apiClient.post(`/mobile/tasks/picks/${pickId}/complete`);
}

export async function startDropTask(dropId: string): Promise<{ data: DropTask }> {
  return apiClient.post(`/mobile/tasks/drops/${dropId}/start`);
}

export async function completeDropTask(
  dropId: string
): Promise<{ data: { drop: DropTask; transaction_completed: boolean } }> {
  return apiClient.post(`/mobile/tasks/drops/${dropId}/complete`);
}

export async function getMyTasks(): Promise<{
  data: { picks: PickTask[]; drops: DropTask[] };
}> {
  return apiClient.get('/mobile/tasks/my');
}

export async function getTaskHistory(): Promise<{
  data: { picks: PickTask[]; drops: DropTask[] };
}> {
  return apiClient.get('/mobile/tasks/history');
}
