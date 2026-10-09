import { create } from "zustand";
import type { AuthUser } from "@/types/auth.types";
import { authService } from "@/services/authService";

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  setAuth: (user: AuthUser, token: string) => void;
  setAccessToken: (token: string) => void;
  clearAuth: () => void;
  initializeAuth: () => Promise<void>;
}

let initPromise: Promise<void> | null = null;

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isInitializing: true,

  setAuth: (user, token) => {
    initPromise = null;
    set({
      user,
      accessToken: token,
      isAuthenticated: true,
      isInitializing: false,
    });
  },

  setAccessToken: (token) =>
    set({
      accessToken: token,
      isAuthenticated: true,
    }),

  clearAuth: () => {
    initPromise = null;
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isInitializing: false,
    });
  },

  initializeAuth: async () => {
    // Avoid re-running initialization if already done
    if (!get().isInitializing && get().isAuthenticated) return;
    if (initPromise) return initPromise;

    initPromise = (async () => {
      try {
        // 1. Check if an active session exists via HttpOnly cookie refresh
        const { access_token } = await authService.refreshToken();
        set({ accessToken: access_token });

        // 2. Fetch authenticated user profile
        const user = await authService.getMe();
        set({
          user,
          accessToken: access_token,
          isAuthenticated: true,
          isInitializing: false,
        });
      } catch {
        // Unauthenticated or expired session
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isInitializing: false,
        });
      } finally {
        initPromise = null;
      }
    })();

    return initPromise;
  },
}));
