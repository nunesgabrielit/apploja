import { api } from "@/services/api";
import type { LoginResponse, RegisterPayload, User } from "@/types/auth";

export async function login(email: string, password: string): Promise<LoginResponse> {
  const payload = new URLSearchParams({
    username: email,
    password
  });
  const { data } = await api.post<LoginResponse>("/auth/login", payload, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    }
  });
  return data;
}

export async function registerCustomer(payload: RegisterPayload): Promise<User> {
  const { data } = await api.post<User>("/auth/register", payload);
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function checkApiHealth(): Promise<boolean> {
  const { data } = await api.get<{ status: string }>("/health");
  return data.status === "ok";
}
