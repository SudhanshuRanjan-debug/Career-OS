/**
 * Settings, Account, Notifications & Security Types.
 * Stage 9: Analytics & Settings.
 */

export interface AccountDetailsResponse {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface AccountUpdateRequest {
  username?: string;
  email?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface NotificationSettingsResponse {
  in_app_alerts: boolean;
  interview_reminders: boolean;
  deadline_reminders: boolean;
  task_reminders: boolean;
}

export interface NotificationSettingsUpdate {
  in_app_alerts?: boolean;
  interview_reminders?: boolean;
  deadline_reminders?: boolean;
  task_reminders?: boolean;
}

export interface DataExportResponse {
  exported_at: string;
  user_id: string;
  email: string;
  data: Record<string, unknown>;
}

export interface DeleteAccountRequest {
  password: string;
}
