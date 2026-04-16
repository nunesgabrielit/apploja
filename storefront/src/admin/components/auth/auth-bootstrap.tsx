"use client";

import { useEffect } from "react";

import { useAuthStore } from "@/admin/store/auth.store";
import { getToken } from "@/utils/token";

export function AuthBootstrap(): null {
  const fetchCurrentUser = useAuthStore((state) => state.fetchCurrentUser);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const user = useAuthStore((state) => state.user);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    if (!user && getToken()) {
      void fetchCurrentUser();
    }
  }, [fetchCurrentUser, isHydrated, user]);

  return null;
}
