"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { Loader2 } from "lucide-react";

import { LoginRoleSwitcher } from "@/components/auth/login-role-switcher";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth.store";
import { getLoginPageCopy, getPostLoginHref } from "@/utils/auth-routing";

export default function ShopLogin() {
  const router = useRouter();
  const loginWithPassword = useAuthStore((state) => state.loginWithPassword);
  const pageCopy = getLoginPageCopy("customer");

  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);

    const formData = new FormData(event.currentTarget);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      const user = await loginWithPassword(email, password);
      router.push(getPostLoginHref(user.role));
    } catch (error) {
      setErrorMsg(error instanceof Error ? error.message : "Erro ao realizar login");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-16rem)] items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-xl border border-slate-100 bg-white p-8 shadow-md">
        <div>
          <p className="text-center text-xs font-semibold uppercase tracking-[0.22em] text-brand-600">
            {pageCopy.eyebrow}
          </p>
          <h2 className="text-center text-3xl font-bold tracking-tight text-slate-900">
            {pageCopy.title}
          </h2>
          <p className="mt-2 text-center text-sm text-slate-600">{pageCopy.description}</p>
          <p className="mt-3 text-center text-sm text-slate-600">
            Ou{" "}
            <Link href="/cliente/cadastro" className="font-medium text-blue-600 hover:text-blue-500">
              crie uma nova conta gratuitamente
            </Link>
          </p>
        </div>

        <LoginRoleSwitcher currentRole="customer" />

        {errorMsg ? <Alert message={errorMsg} /> : null}

        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="space-y-4 rounded-md shadow-sm">
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              placeholder="Seu e-mail"
              label="E-mail"
            />
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              placeholder="Sua senha"
              label="Senha"
            />
          </div>

          <div>
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                pageCopy.submitLabel
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
