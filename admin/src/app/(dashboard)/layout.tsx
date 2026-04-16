import type { ReactNode } from "react";

import { DashboardGuard } from "@/components/auth/dashboard-guard";
import { AdminShell } from "@/components/layout/admin-shell";

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
