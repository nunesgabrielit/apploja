"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { useAuthStore } from "@/store/auth.store";
import { getToken } from "@/utils/token";

interface DashboardGuardProps {
  children: ReactNode;
}

export function DashboardGuard({ children }: DashboardGuardProps): ReactNode {
  const router = useRouter();
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const user = useAuthStore((state) => state.user);
  const fetchCurrentUser = useAuthStore((state) => state.fetchCurrentUser);
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    if (!user) {
      void fetchCurrentUser();
      return;
    }
    if (user.role === "customer") {
      logout();
      router.replace("/login");
    }
  }, [fetchCurrentUser, isHydrated, logout, router, user]);

  if (!isHydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">
        Carregando painel...
      </div>
    );
  }

  if (!getToken() || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">
        Validando sessão...
      </div>
    );
  }

  if (user.role === "customer") {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">
        Validando permissões...
      </div>
    );
  }

  return children;
}
