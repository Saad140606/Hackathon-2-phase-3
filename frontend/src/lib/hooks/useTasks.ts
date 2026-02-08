"use client";

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/lib/hooks/useAuth';
import {
  listTasks,
  createTask as apiCreateTask,
  updateTask as apiUpdateTask,
  partialUpdateTask as apiPartialUpdate,
  deleteTask as apiDeleteTask,
} from '@/lib/api/tasks';
import { Task, TaskCreateRequest, TaskUpdateRequest, TaskListResponse } from '@/types/tasks';
import { PaginationState } from '@/types/ui';

export function useTasks() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({
    currentPage: 1,
    pageSize: 20,
    totalItems: 0,
    totalPages: 1,
    canGoBack: false,
    canGoForward: false,
  });

  const fetchPage = useCallback(async (page = 1, pageSize = 20) => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const res: TaskListResponse = await listTasks(user.id, page, pageSize);
      setTasks(res.items);
      setPagination({
        currentPage: res.page,
        pageSize: res.page_size,
        totalItems: res.total,
        totalPages: res.total_pages,
        canGoBack: res.page > 1,
        canGoForward: res.page < res.total_pages,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    // load initial page when user is available
    if (user) fetchPage(1, pagination.pageSize);
  }, [user, fetchPage]);

  const goToPage = useCallback((page: number) => {
    fetchPage(page, pagination.pageSize);
  }, [fetchPage, pagination.pageSize]);

  const createTask = useCallback(async (data: TaskCreateRequest) => {
    if (!user) throw new Error('Not authenticated');
    setLoading(true);
    try {
      await apiCreateTask(user.id, data);
      await fetchPage(pagination.currentPage, pagination.pageSize);
    } finally {
      setLoading(false);
    }
  }, [user, fetchPage, pagination.currentPage, pagination.pageSize]);

  const updateTask = useCallback(async (taskId: string, data: TaskUpdateRequest) => {
    if (!user) throw new Error('Not authenticated');
    setLoading(true);
    try {
      await apiUpdateTask(user.id, taskId, data);
      await fetchPage(pagination.currentPage, pagination.pageSize);
    } finally {
      setLoading(false);
    }
  }, [user, fetchPage, pagination.currentPage, pagination.pageSize]);

  const toggleComplete = useCallback(async (taskId: string) => {
    if (!user) throw new Error('Not authenticated');
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    setLoading(true);
    try {
      await apiPartialUpdate(user.id, taskId, { is_completed: !task.is_completed });
      // optimistic local update
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, is_completed: !t.is_completed } : t));
    } catch (err: unknown) {
      // on error, refresh entire page
      await fetchPage(pagination.currentPage, pagination.pageSize);
    } finally {
      setLoading(false);
    }
  }, [user, tasks, fetchPage, pagination.currentPage, pagination.pageSize]);

  const deleteTask = useCallback(async (taskId: string) => {
    if (!user) throw new Error('Not authenticated');
    setLoading(true);
    try {
      await apiDeleteTask(user.id, taskId);
      await fetchPage(pagination.currentPage, pagination.pageSize);
    } finally {
      setLoading(false);
    }
  }, [user, fetchPage, pagination.currentPage, pagination.pageSize]);

  return {
    tasks,
    loading,
    error,
    pagination,
    fetchPage,
    goToPage,
    createTask,
    updateTask,
    toggleComplete,
    deleteTask,
  } as const;
}

export default useTasks;
