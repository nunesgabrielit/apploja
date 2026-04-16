import { AxiosError } from "axios";

import type { ApiErrorPayload } from "@/types/auth";

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const payload = error.response?.data as ApiErrorPayload | undefined;
    if (payload?.detail) {
      return payload.detail;
    }
  }
  return fallback;
}
