"use client";

import { AxiosError } from "axios";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { getMe, login } from "@/services/auth.service";
import type { ApiErrorPayload, User } from "@/types/auth";
import { clearToken, getToken, setToken } from "@/utils/token";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isHydrated: boolean;
  error: string | null;
  setHydrated: (value: boolean) => void;
  loginWithPassword: (email: string, password: string) => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

function parseError(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as ApiErrorPayload | undefined)?.detail;
    return detail ?? "Não foi possível concluir a operação.";
  }
  return "Erro inesperado. Tente novamente.";
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isLoading: false,
      isHydrated: false,
      error: null,
      setHydrated: (value) => set({ isHydrated: value }),
      loginWithPassword: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await login(email, password);
          setToken(response.access_token);
          set({ user: response.user, isLoading: false });
        } catch (error) {
          set({ isLoading: false, error: parseError(error) });
          throw error;
        }
      },
      fetchCurrentUser: async () => {
        const token = getToken();
        if (!token) {
          set({ user: null });
          return;
        }
        set({ isLoading: true, error: null });
        try {
          const user = await getMe();
          set({ user, isLoading: false });
        } catch (error) {
          clearToken();
          set({ user: null, isLoading: false, error: parseError(error) });
        }
      },
      logout: () => {
        clearToken();
        set({ user: null, error: null, isLoading: false });
      },
      clearError: () => set({ error: null })
    }),
    {
      name: "wm-admin-auth",
      partialize: (state) => ({ user: state.user }),
      storage: createJSONStorage(() => localStorage),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated(true);
        if (getToken() && !state?.user) {
          void state?.fetchCurrentUser();
        }
      }
    }
  )
);
