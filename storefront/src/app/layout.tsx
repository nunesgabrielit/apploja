import type { Metadata } from "next";
import type { ReactNode } from "react";

import { ShopFooter } from "@/components/shop/footer";
import { ShopHeader } from "@/components/shop/header";

import "./globals.css";

export const metadata: Metadata = {
  title: "WM Distribuidora",
  description: "O melhor catálogo para sua distribuidora"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <div className="flex min-h-screen flex-col bg-slate-50">
          <ShopHeader />
          <main className="flex-1">{children}</main>
          <ShopFooter />
        </div>
      </body>
    </html>
  );
}
