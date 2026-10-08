export type NotificationType =
  | "INTERVIEW_REMINDER"
  | "TASK_DUE"
  | "FOLLOW_UP_DUE"
  | "DEADLINE"
  | "SYSTEM";

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  body?: string | null;
  notification_type: NotificationType;
  is_read: boolean;
  read_at?: string | null;
  related_type?: string | null;
  related_id?: string | null;
  created_at: string;
}

export interface NotificationUnreadCountResponse {
  unread_count: number;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
}
