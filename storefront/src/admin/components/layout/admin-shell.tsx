"use client";

import type { ReactNode } from "react";
import { useState } from "react";

import { Header } from "@/admin/components/layout/header";
import { Sidebar } from "@/admin/components/layout/sidebar";

interface AdminShellProps {
  children: ReactNode;
}

export function AdminShell({ children }: AdminShellProps): ReactNode {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[linear-gradient(180deg,#eef5ff_0%,#f8fbff_24%,#f4f7fb_100%)]">
      <Sidebar
        collapsed={sidebarCollapsed}
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
        onToggleCollapse={() => setSidebarCollapsed((current) => !current)}
      />

      <div className="flex min-h-screen flex-1 flex-col overflow-hidden">
        <Header onOpenMobileSidebar={() => setMobileSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
