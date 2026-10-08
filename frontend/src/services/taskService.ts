/**
 * Tasks API Client Service.
 * Stage 8: Tasks, Calendar & Notifications.
 */

import { apiClient } from "@/lib/axios";
import type {
  Task,
  TaskCreateInput,
  TaskListResponse,
  TaskPriority,
  TaskRelatedType,
  TaskStatus,
  TaskUpdateInput,
} from "@/types/task.types";

export interface TaskFilterParams {
  filter?: "all" | "today" | "upcoming" | "completed";
  status?: TaskStatus;
  priority?: TaskPriority;
  related_type?: TaskRelatedType;
  application_id?: string;
  interview_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const taskService = {
  async listTasks(params?: TaskFilterParams): Promise<TaskListResponse> {
    const res = await apiClient.get<TaskListResponse>("/tasks", { params });
    return res.data;
  },

  async createTask(data: TaskCreateInput): Promise<Task> {
    const res = await apiClient.post<Task>("/tasks", data);
    return res.data;
  },

  async getTask(id: string): Promise<Task> {
    const res = await apiClient.get<Task>(`/tasks/${id}`);
    return res.data;
  },

  async updateTask(id: string, data: TaskUpdateInput): Promise<Task> {
    const res = await apiClient.put<Task>(`/tasks/${id}`, data);
    return res.data;
  },

  async completeTask(id: string): Promise<Task> {
    const res = await apiClient.post<Task>(`/tasks/${id}/complete`);
    return res.data;
  },

  async deleteTask(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/tasks/${id}`);
    return res.data;
  },

  async listApplicationTasks(applicationId: string): Promise<Task[]> {
    const res = await apiClient.get<Task[]>(`/applications/${applicationId}/tasks`);
    return res.data;
  },
};
