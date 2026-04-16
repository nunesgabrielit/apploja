"use client";

import { Lock, Mail } from "lucide-react";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth.store";
import { getToken } from "@/utils/token";

export default function LoginPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const loginWithPassword = useAuthStore((state) => state.loginWithPassword);
  const clearError = useAuthStore((state) => state.clearError);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    if (getToken() && user) {
      router.replace("/dashboard");
    }
  }, [isHydrated, router, user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    clearError();
    try {
      await loginWithPassword(email, password);
      router.replace("/dashboard");
    } catch {
      return;
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-widest text-brand-600">
            Painel Administrativo
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900">WM Distribuidora</h1>
          <p className="mt-2 text-sm text-slate-500">
            Faça login para acessar os módulos operacionais da plataforma.
          </p>
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

          {error ? <Alert message={error} /> : null}

          <Button type="submit" fullWidth disabled={isLoading}>
            {isLoading ? "Entrando..." : "Entrar no painel"}
          </Button>
        </form>
      </section>
    </main>
  );
}
