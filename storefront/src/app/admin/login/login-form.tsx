"use client";

import { Lock, Mail } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { useAuthStore } from "@/admin/store/auth.store";
import { LoginRoleSwitcher } from "@/components/auth/login-role-switcher";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getToken } from "@/utils/token";
import {
  getLoginPageCopy,
  getPostLoginHref,
  normalizeLoginRole,
} from "@/utils/auth-routing";

export function AdminLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const user = useAuthStore((state) => state.user);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const loginWithPassword = useAuthStore((state) => state.loginWithPassword);
  const clearError = useAuthStore((state) => state.clearError);

  const loginRole = normalizeLoginRole(searchParams.get("role"), "admin");
  const currentRole = loginRole === "customer" ? "admin" : loginRole;
  const pageCopy = getLoginPageCopy(currentRole);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [accessError, setAccessError] = useState<string | null>(null);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    if (getToken() && user) {
      router.replace(getPostLoginHref(user.role));
    }
  }, [isHydrated, router, user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    clearError();
    setAccessError(null);

    try {
      const loggedUser = await loginWithPassword(email, password);
      if (loggedUser.role === "customer") {
        useAuthStore.getState().logout();
        setAccessError("Esta conta e de cliente. Use a opcao de acesso do cliente.");
        return;
      }
      router.replace(getPostLoginHref(loggedUser.role));
    } catch {
      return;
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-widest text-brand-600">
            {pageCopy.eyebrow}
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900">{pageCopy.title}</h1>
          <p className="mt-2 text-sm text-slate-500">{pageCopy.description}</p>
        </div>

        <div className="mb-6">
          <LoginRoleSwitcher currentRole={currentRole} />
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="relative">
            <span className="pointer-events-none absolute left-3 top-9 text-slate-400">
              <Mail size={16} />
            </span>
            <Input
              id="email"
              type="email"
              label="E-mail"
              autoComplete="email"
              placeholder="admin@wmdistribuidora.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="pl-9"
              required
            />
          </div>

          <div className="relative">
            <span className="pointer-events-none absolute left-3 top-9 text-slate-400">
              <Lock size={16} />
            </span>
            <Input
              id="password"
              type="password"
              label="Senha"
              autoComplete="current-password"
              placeholder="Digite sua senha"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="pl-9"
              required
            />
          </div>

          {accessError ? <Alert message={accessError} /> : null}
          {!accessError && error ? <Alert message={error} /> : null}

          <Button type="submit" fullWidth disabled={isLoading}>
            {isLoading ? "Entrando..." : pageCopy.submitLabel}
          </Button>
        </form>
      </section>
    </main>
  );
}
