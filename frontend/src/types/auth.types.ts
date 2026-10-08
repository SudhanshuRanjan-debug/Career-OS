export interface AuthUser {
  id: string;
  email: string;
  username: string;
  role: "CANDIDATE" | "HIRER";
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  role?: "CANDIDATE" | "HIRER";
  organization_name?: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  new_password: string;
}

export interface UserSession {
  id: string;
  created_at: string;
  expires_at: string;
  user_agent?: string | null;
  ip_address?: string | null;
  is_current: boolean;
}
