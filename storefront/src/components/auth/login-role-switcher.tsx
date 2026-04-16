"use client";

import Link from "next/link";

import { LOGIN_OPTIONS, type LoginRole, getLoginHref } from "@/utils/auth-routing";
import { cn } from "@/utils/cn";

interface LoginRoleSwitcherProps {
  currentRole: LoginRole;
}

export function LoginRoleSwitcher({ currentRole }: LoginRoleSwitcherProps) {
  return (
    <div className="space-y-3">
      <p className="text-center text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        Escolha como deseja entrar
      </p>
      <div className="grid gap-2 sm:grid-cols-3">
        {LOGIN_OPTIONS.map((option) => {
          const isActive = option.role === currentRole;

          return (
            <Link
              key={option.role}
              href={getLoginHref(option.role)}
              className={cn(
                "rounded-xl border px-3 py-3 text-left transition",
                isActive
                  ? "border-brand-500 bg-brand-50 text-brand-700 shadow-sm"
                  : "border-slate-200 bg-white text-slate-700 hover:border-brand-200 hover:bg-slate-50"
              )}
            >
              <span className="block text-sm font-semibold">{option.label}</span>
              <span className="mt-1 block text-xs leading-5 text-slate-500">{option.hint}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
