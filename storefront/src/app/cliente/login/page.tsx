"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { Loader2, Mail, Lock } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ShopLogin() {
  const router = useRouter();
  const loginWithPassword = useAuthStore((s) => s.loginWithPassword);
  
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleLogin(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    
    const formData = new FormData(e.currentTarget);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      const user = await loginWithPassword(email, password);
      // Se não for customer, deslogar e bloquear
      if (user.role !== "customer") {
        useAuthStore.getState().logout();
        setErrorMsg("Esta conta é de administrador/funcionário. Use o painel admin em localhost:3000.");
        return;
      }
      router.push("/");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Erro ao realizar login");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-16rem)] items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-white p-8 shadow-md border border-slate-100">
        <div>
          <h2 className="text-center text-3xl font-bold tracking-tight text-slate-900">
            Acesse sua conta
          </h2>
          <p className="mt-2 text-center text-sm text-slate-600">
            Ou{" "}
            <Link href="/cliente/cadastro" className="font-medium text-blue-600 hover:text-blue-500">
              crie uma nova conta gratuitamente
            </Link>
          </p>
        </div>
        
        {errorMsg && (
          <Alert message={errorMsg} />
        )}

        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="space-y-4 rounded-md shadow-sm">
            <div>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                placeholder="Seu e-mail"
                label="E-mail"
              />
            </div>
            <div>
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
          </div>

          <div>
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                "Entrar"
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
