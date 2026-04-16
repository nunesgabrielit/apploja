import type { ReactNode } from "react";

import { DashboardGuard } from "@/admin/components/auth/dashboard-guard";
import { AdminShell } from "@/admin/components/layout/admin-shell";

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps): ReactNode {
  return (
    <DashboardGuard>
      <AdminShell>{children}</AdminShell>
    </DashboardGuard>
  );
}
