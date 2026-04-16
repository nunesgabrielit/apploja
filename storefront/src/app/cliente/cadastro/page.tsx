"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { Loader2, Mail, Lock, User, Phone } from "lucide-react";
import { registerCustomer } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ShopRegister() {
  const router = useRouter();
  const loginWithPassword = useAuthStore((s) => s.loginWithPassword);
  
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleRegister(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    
    const formData = new FormData(e.currentTarget);
    const name = formData.get("name") as string;
    const email = formData.get("email") as string;
    const phone = formData.get("phone") as string;
    const password = formData.get("password") as string;

    try {
      // 1. Cadastra o cliente
      await registerCustomer({
        name,
        email,
        password,
        phone: phone || undefined,
      });

      // 2. Faz login automaticamente
      await loginWithPassword(email, password);
      
      // 3. Redireciona para a home
      router.push("/");
    } catch (err: any) {
      setErrorMsg(err.message || "Erro ao criar conta. Verifique os dados e tente novamente.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-16rem)] items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-white p-8 shadow-md border border-slate-100">
        <div>
          <h2 className="text-center text-3xl font-bold tracking-tight text-slate-900">
            Criar conta
          </h2>
          <p className="mt-2 text-center text-sm text-slate-600">
            Já tem uma conta?{" "}
            <Link href="/cliente/login" className="font-medium text-blue-600 hover:text-blue-500">
              Faça login aqui
            </Link>
          </p>
        </div>
        
        {errorMsg && (
          <Alert message={errorMsg} />
        )}

        <form className="mt-8 space-y-6" onSubmit={handleRegister}>
          <div className="space-y-4 rounded-md shadow-sm">
            <div>
              <Input
                id="name"
                name="name"
                type="text"
                autoComplete="name"
                required
                placeholder="Seu nome completo"
                label="Nome completo"
              />
            </div>
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
                id="phone"
                name="phone"
                type="tel"
                autoComplete="tel"
                placeholder="(00) 00000-0000"
                label="Telefone (Opcional)"
              />
            </div>
            <div>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                placeholder="Sua senha (mínimo 8 caracteres)"
                label="Senha"
                minLength={8}
              />
            </div>
          </div>

          <div>
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Criando conta...
                </>
              ) : (
                "Cadastrar"
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
