import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthBootstrap } from "@/admin/components/auth/auth-bootstrap";

export const metadata: Metadata = {
  title: "WM Distribuidora | Admin",
  description: "Painel administrativo da WM Distribuidora"
};

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps): ReactNode {
  return (
    <>
      <AuthBootstrap />
      {children}
    </>
  );
}
