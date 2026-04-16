import { Suspense } from "react";

import { AdminLoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10">
          <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <p className="text-center text-sm text-slate-500">Carregando acesso...</p>
          </section>
        </main>
      }
    >
      <AdminLoginForm />
    </Suspense>
  );
}
