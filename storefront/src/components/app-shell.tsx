"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { ShopFooter } from "@/components/shop/footer";
import { ShopHeader } from "@/components/shop/header";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps): ReactNode {
  const pathname = usePathname();
  const isAdminRoute = pathname.startsWith("/admin");

  if (isAdminRoute) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <ShopHeader />
      <main className="flex-1">{children}</main>
      <ShopFooter />
    </div>
  );
}
