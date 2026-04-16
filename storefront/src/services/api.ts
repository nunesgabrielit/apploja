import axios, { AxiosError } from "axios";

import { clearToken, getToken } from "@/utils/token";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

export function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data;
    if (typeof responseData === "object" && responseData !== null) {
      const detail = Reflect.get(responseData, "detail");
      if (typeof detail === "string" && detail.trim()) {
        return detail;
      }

      const message = Reflect.get(responseData, "message");
      if (typeof message === "string" && message.trim()) {
        return message;
      }
    }

    if (typeof error.message === "string" && error.message.trim()) {
      return error.message;
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return fallbackMessage;
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearToken();
      if (typeof window !== "undefined" && window.location.pathname !== "/cliente/login") {
        window.location.href = "/cliente/login";
      }
    }
    return Promise.reject(error);
  }
);
