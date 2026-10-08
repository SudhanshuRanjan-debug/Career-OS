import { apiClient } from "@/lib/axios";
import type {
  AuthResponse,
  AuthUser,
  ForgotPasswordPayload,
  LoginPayload,
  RefreshResponse,
  RegisterPayload,
  ResetPasswordPayload,
  UserSession,
} from "@/types/auth.types";

export const authService = {
  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>("/auth/register", payload);
    return response.data;
  },

  async login(payload: LoginPayload): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>("/auth/login", payload);
    return response.data;
  },

  async refreshToken(): Promise<RefreshResponse> {
    const response = await apiClient.post<RefreshResponse>("/auth/refresh");
    return response.data;
  },

  async logout(): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>("/auth/logout");
    return response.data;
  },

  async getMe(): Promise<AuthUser> {
    const response = await apiClient.get<AuthUser>("/auth/me");
    return response.data;
  },

  async forgotPassword(payload: ForgotPasswordPayload): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>("/auth/forgot-password", payload);
    return response.data;
  },

  async resetPassword(payload: ResetPasswordPayload): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>("/auth/reset-password", payload);
    return response.data;
  },

  async getSessions(): Promise<UserSession[]> {
    const response = await apiClient.get<UserSession[]>("/auth/sessions");
    return response.data;
  },

  async revokeSession(sessionId: string): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(`/auth/sessions/${sessionId}`);
    return response.data;
  },
};
