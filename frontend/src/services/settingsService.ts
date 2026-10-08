/**
 * Settings API Client Service.
 * Stage 9: Analytics & Settings.
 */

import { apiClient } from "@/lib/axios";
import type { UserSession } from "@/types/auth.types";
import type {
  AccountDetailsResponse,
  AccountUpdateRequest,
  ChangePasswordRequest,
  NotificationSettingsResponse,
  NotificationSettingsUpdate,
  DataExportResponse,
  DeleteAccountRequest,
} from "@/types/settings.types";

export const settingsService = {
  async getAccount(): Promise<AccountDetailsResponse> {
    const res = await apiClient.get<AccountDetailsResponse>("/settings/account");
    return res.data;
  },

  async updateAccount(data: AccountUpdateRequest): Promise<AccountDetailsResponse> {
    const res = await apiClient.put<AccountDetailsResponse>("/settings/account", data);
    return res.data;
  },

  async changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
    const res = await apiClient.put<{ message: string }>("/settings/security/password", data);
    return res.data;
  },

  async getSessions(): Promise<UserSession[]> {
    const res = await apiClient.get<UserSession[]>("/settings/sessions");
    return res.data;
  },

  async revokeSession(sessionId: string): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>(`/settings/sessions/${sessionId}`);
    return res.data;
  },

  async getNotificationSettings(): Promise<NotificationSettingsResponse> {
    const res = await apiClient.get<NotificationSettingsResponse>("/settings/notifications");
    return res.data;
  },

  async updateNotificationSettings(
    data: NotificationSettingsUpdate
  ): Promise<NotificationSettingsResponse> {
    const res = await apiClient.put<NotificationSettingsResponse>("/settings/notifications", data);
    return res.data;
  },

  async exportData(): Promise<DataExportResponse> {
    const res = await apiClient.post<DataExportResponse>("/settings/data-export");
    return res.data;
  },

  async deleteAccount(data: DeleteAccountRequest): Promise<{ message: string }> {
    const res = await apiClient.delete<{ message: string }>("/settings/account", { data });
    return res.data;
  },
};
