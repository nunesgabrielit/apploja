"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useMemo } from "react";
import {
  Boxes,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  LayoutDashboard,
  Package,
  ShieldCheck,
  Truck,
  Users,
  X
} from "lucide-react";

import { cn } from "@/utils/cn";

interface NavItem {
  label: string;
  href: string;
  icon: ReactNode;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

interface SidebarProps {
  collapsed: boolean;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  onToggleCollapse: () => void;
}

export function Sidebar({
  collapsed,
  mobileOpen,
  onCloseMobile,
  onToggleCollapse
}: SidebarProps): ReactNode {
  const pathname = usePathname();

  const navGroups = useMemo<NavGroup[]>(
    () => [
      {
        title: "Dashboards",
        items: [{ label: "Visao Geral", href: "/admin/dashboard", icon: <LayoutDashboard size={18} /> }]
      },
      {
        title: "Operacional",
        items: [
          { label: "Pedidos", href: "/admin/dashboard/pedidos", icon: <ClipboardList size={18} /> },
          { label: "Frete", href: "/admin/dashboard/frete", icon: <Truck size={18} /> },
          { label: "Estoque", href: "/admin/dashboard/estoque", icon: <Package size={18} /> },
          { label: "Produtos", href: "/admin/dashboard/produtos", icon: <Boxes size={18} /> }
        ]
      },
      {
        title: "Configuracoes",
        items: [
          { label: "Funcionarios", href: "/admin/dashboard/funcionarios", icon: <Users size={18} /> }
        ]
      }
    ],
    []
  );

  return (
    <>
      <div
        className={cn(
          "fixed inset-0 z-30 bg-slate-950/45 backdrop-blur-sm transition-opacity md:hidden",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={onCloseMobile}
      />

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex h-screen flex-col border-r border-white/10 bg-[linear-gradient(180deg,#0f4fd6_0%,#1257e6_28%,#163fc7_100%)] text-white shadow-[0_20px_80px_rgba(15,79,214,0.28)] transition-all duration-300 md:sticky md:top-0",
          collapsed ? "md:w-24" : "md:w-72",
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          "w-72"
        )}
      >
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/14 shadow-inner shadow-white/10">
              <ShieldCheck size={22} className="text-white" />
            </div>
            <div className={cn("min-w-0", collapsed && "md:hidden")}>
              <p className="text-[11px] uppercase tracking-[0.22em] text-blue-100/70">Painel WM</p>
              <h2 className="truncate text-lg font-semibold text-white">Distribuidora</h2>
            </div>
          </div>

          <button
            type="button"
            onClick={mobileOpen ? onCloseMobile : onToggleCollapse}
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/10 text-white transition hover:bg-white/15 md:hidden"
          >
            <X size={18} />
          </button>
        </div>

        <div className="hidden border-b border-white/10 px-5 py-4 md:block">
          <button
            type="button"
            onClick={onToggleCollapse}
            className={cn(
              "inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm font-medium text-white transition hover:bg-white/15",
              collapsed && "w-full justify-center px-0"
            )}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            <span className={cn(collapsed && "hidden")}>
              {collapsed ? "Expandir" : "Recolher menu"}
            </span>
          </button>
        </div>

        <nav className="flex flex-1 flex-col gap-7 overflow-y-auto px-4 py-6">
          {navGroups.map((group) => (
            <div key={group.title} className="space-y-2">
              <p
                className={cn(
                  "px-3 text-[11px] font-semibold uppercase tracking-[0.24em] text-blue-100/65",
                  collapsed && "md:hidden"
                )}
              >
                {group.title}
              </p>

              <div className="space-y-1.5">
                {group.items.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(`${item.href}/`);

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      onClick={onCloseMobile}
                      className={cn(
                        "group flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition-all",
                        active
                          ? "bg-white text-brand-700 shadow-[0_12px_30px_rgba(9,30,66,0.12)]"
                          : "text-blue-50/88 hover:bg-white/10 hover:text-white",
                        collapsed && "md:justify-center"
                      )}
                    >
                      <span
                        className={cn(
                          "flex h-10 w-10 items-center justify-center rounded-xl transition",
                          active
                            ? "bg-brand-50 text-brand-700"
                            : "bg-white/10 text-blue-50 group-hover:bg-white/15"
                        )}
                      >
                        {item.icon}
                      </span>
                      <span className={cn("truncate", collapsed && "md:hidden")}>{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-white/10 p-4">
          <div
            className={cn(
              "rounded-2xl border border-white/10 bg-white/10 p-4 text-blue-50/90",
              collapsed && "md:px-2 md:py-3"
            )}
          >
            <p className={cn("text-xs uppercase tracking-[0.22em] text-blue-100/70", collapsed && "md:hidden")}>
              Ambiente
            </p>
            <p className={cn("mt-2 text-sm font-semibold text-white", collapsed && "md:hidden")}>
              Operacao Local
            </p>
            <p className={cn("mt-1 text-xs text-blue-50/75", collapsed && "md:hidden")}>
              Catalogo, estoque e pedidos em um unico painel.
            </p>
            {collapsed ? (
              <div className="hidden h-10 items-center justify-center rounded-xl bg-white/10 text-white md:flex">
                <ShieldCheck size={18} />
              </div>
            ) : null}
          </div>
        </div>
      </aside>
    </>
  );
}
