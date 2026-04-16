export type UserRole = "admin" | "employee" | "customer";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ApiErrorPayload {
  detail?: string;
  code?: string;
  errors?: unknown;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  phone?: string;
}

