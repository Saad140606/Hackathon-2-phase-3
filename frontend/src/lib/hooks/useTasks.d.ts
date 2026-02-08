declare module '@/lib/hooks/useTasks' {
  import { Task, TaskCreateRequest, TaskUpdateRequest } from '@/types/tasks';
  import { PaginationState } from '@/types/ui';
  export function useTasks(): {
    tasks: Task[];
    loading: boolean;
    error: string | null;
    pagination: PaginationState;
    fetchPage: (page?: number) => Promise<void>;
    goToPage: (page: number) => void;
    createTask: (data: TaskCreateRequest) => Promise<void>;
    updateTask: (id: string, data: TaskUpdateRequest) => Promise<void>;
    toggleComplete: (id: string) => Promise<void>;
    deleteTask: (id: string) => Promise<void>;
  };
  export default useTasks;
}
