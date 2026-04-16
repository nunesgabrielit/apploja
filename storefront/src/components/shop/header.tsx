"use client";

import Link from "next/link";
import {
  Briefcase,
  ChevronDown,
  LogOut,
  Search,
  ShieldCheck,
  ShoppingCart,
  User as UserIcon,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { useAuthStore } from "@/store/auth.store";
import { useCartStore } from "@/store/cart.store";
import { cn } from "@/utils/cn";
import { LOGIN_OPTIONS, getLoginHref, getPostLoginHref } from "@/utils/auth-routing";

export function ShopHeader() {
  const { user, isHydrated } = useAuthStore();
  const { cart, refreshCart, clearCartState } = useCartStore();
  const [mounted, setMounted] = useState(false);
  const [loginPanelOpen, setLoginPanelOpen] = useState(false);
  const loginPanelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!loginPanelRef.current?.contains(event.target as Node)) {
        setLoginPanelOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setLoginPanelOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  useEffect(() => {
    if (!mounted || !isHydrated) {
      return;
    }

    if (user?.role === "customer") {
      void refreshCart().catch(() => undefined);
      return;
    }

    clearCartState();
  }, [clearCartState, isHydrated, mounted, refreshCart, user]);

  const cartCount = cart?.total_items ?? 0;

  function handleAreaNavigation(targetRole: (typeof LOGIN_OPTIONS)[number]["role"]) {
    setLoginPanelOpen(false);

    if (user?.role === targetRole) {
      window.location.href = getPostLoginHref(targetRole);
      return;
    }

    if (user) {
      useAuthStore.getState().logout();
    }

    window.location.href = getLoginHref(targetRole);
  }

  function getLoginIcon(role: (typeof LOGIN_OPTIONS)[number]["role"]) {
    switch (role) {
      case "admin":
        return <ShieldCheck className="h-4 w-4 text-brand-600" />;
      case "employee":
        return <Briefcase className="h-4 w-4 text-brand-600" />;
      default:
        return <UserIcon className="h-4 w-4 text-brand-600" />;
    }
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur">
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
            <div className="relative" ref={loginPanelRef}>
              <button
                type="button"
                onClick={() => setLoginPanelOpen((current) => !current)}
                className={cn(
                  "inline-flex items-center gap-1 text-sm font-medium text-slate-700 transition hover:text-blue-600",
                  loginPanelOpen && "text-blue-600"
                )}
                aria-expanded={loginPanelOpen}
                aria-haspopup="menu"
              >
                Areas
                <ChevronDown
                  className={cn("h-4 w-4 transition-transform", loginPanelOpen && "rotate-180")}
                />
              </button>

              {loginPanelOpen ? (
                <div className="absolute right-0 top-full z-50 mt-3 w-80 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl">
                  <div className="border-b border-slate-100 px-2 pb-3">
                    <p className="text-sm font-semibold text-slate-900">Escolha uma area</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      Clique para acessar a area do cliente, dos funcionarios ou do administrador.
                    </p>
                  </div>

                  <div className="mt-3 space-y-2">
                    {LOGIN_OPTIONS.map((option) => (
                      <button
                        key={option.role}
                        type="button"
                        onClick={() => handleAreaNavigation(option.role)}
                        className="flex w-full items-start gap-3 rounded-xl border border-slate-200 px-3 py-3 text-left transition hover:border-brand-200 hover:bg-slate-50"
                      >
                        <span className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-full bg-brand-50">
                          {getLoginIcon(option.role)}
                        </span>
                        <span className="min-w-0">
                          <span className="block text-sm font-semibold text-slate-900">
                            {option.label}
                          </span>
                          <span className="mt-1 block text-xs leading-5 text-slate-500">
                            {option.hint}
                          </span>
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {mounted && isHydrated ? (
            user ? (
              <div className="flex items-center space-x-4">
                <Link
                  href={getPostLoginHref(user.role)}
                  className="flex items-center text-sm font-medium text-slate-700 transition-colors hover:text-blue-600"
                >
                  <UserIcon className="mr-2 h-5 w-5" />
                  <span className="hidden sm:inline-block">Ola, {user.name.split(" ")[0]}</span>
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    useAuthStore.getState().logout();
                    window.location.href = "/";
                  }}
                  className="text-slate-500 transition-colors hover:text-red-600"
                  title="Sair"
                >
                  <LogOut className="h-5 w-5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  href="/cliente/cadastro"
                  className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                >
                  Cadastrar
                </Link>
              </div>
            )
          ) : (
            <div className="h-5 w-24 animate-pulse rounded bg-slate-200" />
          )}

          <Link href="/carrinho" className="group flex items-center p-2">
            <ShoppingCart className="h-6 w-6 flex-shrink-0 text-slate-400 group-hover:text-slate-500" />
            <span className="ml-2 text-sm font-medium text-slate-700 group-hover:text-slate-800">
              {cartCount}
            </span>
          </Link>
        </div>
      </div>
    </header>
  );
}
