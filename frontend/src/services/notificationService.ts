/**
 * In-App Notifications API Client Service.
 * Stage 8: Tasks, Calendar & Notifications.
 */

import { apiClient } from "@/lib/axios";
import type {
  Notification,
  NotificationListResponse,
  NotificationUnreadCountResponse,
} from "@/types/notification.types";

export interface NotificationFilterParams {
  is_read?: boolean;
  page?: number;
  page_size?: number;
}

export const notificationService = {
  async listNotifications(params?: NotificationFilterParams): Promise<NotificationListResponse> {
    const res = await apiClient.get<NotificationListResponse>("/notifications", { params });
    return res.data;
  },

  async getUnreadCount(): Promise<NotificationUnreadCountResponse> {
    const res = await apiClient.get<NotificationUnreadCountResponse>("/notifications/unread-count");
    return res.data;
  },

  async markAsRead(id: string): Promise<Notification> {
    const res = await apiClient.post<Notification>(`/notifications/${id}/read`);
    return res.data;
  },

  async markAllAsRead(): Promise<{ message: string }> {
    const res = await apiClient.post<{ message: string }>("/notifications/read-all");
    return res.data;
  },

  async deleteNotification(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/notifications/${id}`);
    return res.data;
  },
};
