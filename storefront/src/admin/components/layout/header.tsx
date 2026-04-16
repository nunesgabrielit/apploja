"use client";

import { LogOut, Menu, Shield } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/admin/store/auth.store";

interface HeaderProps {
  onOpenMobileSidebar: () => void;
}

function buildPageTitle(pathname: string): { title: string; description: string } {
  if (pathname.startsWith("/admin/dashboard/produtos")) {
    return {
      title: "Catalogo Operacional",
      description: "Gerencie produtos, codigos internos e visibilidade comercial."
    };
  }

  if (pathname.startsWith("/admin/dashboard/estoque")) {
    return {
      title: "Controle de Estoque",
      description: "Acompanhe disponibilidade, itens criticos e reposicoes."
    };
  }

  if (pathname.startsWith("/admin/dashboard/pedidos")) {
    return {
      title: "Central de Pedidos",
      description: "Monitore o fluxo operacional e acompanhe a carteira de vendas."
    };
  }

  if (pathname.startsWith("/admin/dashboard/frete")) {
    return {
      title: "Regras de Frete",
      description: "Configure cobertura por CEP e mantenha o calculo de entrega consistente."
    };
  }

  if (pathname.startsWith("/admin/dashboard/funcionarios")) {
    return {
      title: "Equipe Interna",
      description: "Visualize usuarios operacionais e acompanhe a distribuicao do trabalho."
    };
  }

  return {
    title: "Painel Administrativo",
    description: "Gestao comercial e operacional da WM Distribuidora."
  };
}

export function Header({ onOpenMobileSidebar }: HeaderProps): ReactNode {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const pageCopy = buildPageTitle(pathname);

  const handleLogout = (): void => {
    logout();
    router.replace("/admin/login");
  };

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/88 backdrop-blur-xl">
      <div className="flex items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onOpenMobileSidebar}
            className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-brand-200 hover:text-brand-700 md:hidden"
          >
            <Menu size={20} />
          </button>

          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-500">
              WM Distribuidora
            </p>
            <h1 className="truncate text-lg font-semibold text-slate-900">{pageCopy.title}</h1>
            <p className="truncate text-sm text-slate-500">{pageCopy.description}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 shadow-sm sm:flex">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-50 text-brand-700">
              <Shield size={18} />
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-slate-900">{user?.name ?? "Usuario"}</p>
              <p className="text-xs uppercase tracking-wide text-slate-500">{user?.role ?? "perfil"}</p>
            </div>
          </div>

          <Button variant="secondary" onClick={handleLogout} className="rounded-2xl px-4 py-2.5">
            <span className="mr-2">
              <LogOut size={16} />
            </span>
            Sair
          </Button>
        </div>
      </div>
    </header>
  );
}
