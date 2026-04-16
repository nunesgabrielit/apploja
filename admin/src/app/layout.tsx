import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthBootstrap } from "@/components/auth/auth-bootstrap";

import "./globals.css";

export const metadata: Metadata = {
  title: "WM Distribuidora | Admin",
  description: "Painel administrativo da WM Distribuidora"
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps): ReactNode {
  return (
    <html lang="pt-BR">
      <body>
        <AuthBootstrap />
        {children}
      </body>
    </html>
  );
}
