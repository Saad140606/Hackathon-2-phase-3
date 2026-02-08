import apiClient from './client';
import {
  Task,
  TaskListResponse,
  TaskCreateRequest,
  TaskUpdateRequest,
} from '@/types/tasks';

function authHeader(token?: string) {
  const t = token ?? (typeof window !== 'undefined' ? localStorage.getItem('access_token') : null);
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function listTasks(userId: string, page = 1, pageSize = 20) {
  const res = await apiClient.get<TaskListResponse>(`/users/${userId}/tasks`, {
    params: { page, page_size: pageSize },
    headers: authHeader(),
  });
  return res.data;
}

export async function getTask(userId: string, taskId: string) {
  const res = await apiClient.get<Task>(`/users/${userId}/tasks/${taskId}`, {
    headers: authHeader(),
  });
  return res.data;
}

export async function createTask(userId: string, data: TaskCreateRequest) {
  const res = await apiClient.post<Task>(`/users/${userId}/tasks`, data, {
    headers: authHeader(),
  });
  return res.data;
}

export async function updateTask(userId: string, taskId: string, data: TaskUpdateRequest) {
  const res = await apiClient.put<Task>(`/users/${userId}/tasks/${taskId}`, data, {
    headers: authHeader(),
  });
  return res.data;
}

export async function partialUpdateTask(userId: string, taskId: string, data: Partial<TaskUpdateRequest>) {
  const res = await apiClient.patch<Task>(`/users/${userId}/tasks/${taskId}`, data, {
    headers: authHeader(),
  });
  return res.data;
}

export async function deleteTask(userId: string, taskId: string) {
  await apiClient.delete(`/users/${userId}/tasks/${taskId}`, {
    headers: authHeader(),
  });
}
