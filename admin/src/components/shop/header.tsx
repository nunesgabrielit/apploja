"use client";

import Link from "next/link";
import { Search, ShoppingCart, User as UserIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth.store";

export function ShopHeader() {
  const { user, isHydrated } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center">
          <Link href="/" className="text-xl font-bold text-blue-600">
            WM Distribuidora
          </Link>
        </div>

        <div className="hidden flex-1 items-center justify-center px-8 md:flex">
          <div className="relative w-full max-w-md">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <Search className="h-4 w-4 text-slate-400" />
            </div>
            <input
              type="search"
              placeholder="Buscar produtos..."
              className="block w-full rounded-md border border-slate-300 bg-slate-50 py-2 pl-10 pr-3 text-sm placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex items-center space-x-6">
          {mounted && isHydrated ? (
            user ? (
              <Link
                href={user.role === "customer" ? "/perfil" : "/dashboard"}
                className="flex items-center text-sm font-medium text-slate-700 hover:text-blue-600"
              >
                <UserIcon className="mr-2 h-5 w-5" />
                <span className="hidden sm:inline-block">Olá, {user.name.split(" ")[0]}</span>
              </Link>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  href="/cliente/login"
                  className="text-sm font-medium text-slate-700 hover:text-blue-600"
                >
                  Entrar
                </Link>
                <Link
                  href="/cliente/cadastro"
                  className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                >
                  Cadastrar
                </Link>
              </div>
            )
          ) : (
            <div className="h-5 w-24 animate-pulse rounded bg-slate-200"></div>
          )}

          <Link href="/carrinho" className="group flex items-center p-2">
            <ShoppingCart className="h-6 w-6 flex-shrink-0 text-slate-400 group-hover:text-slate-500" />
            <span className="ml-2 text-sm font-medium text-slate-700 group-hover:text-slate-800">
              0
            </span>
          </Link>
        </div>
      </div>
    </header>
  );
}
