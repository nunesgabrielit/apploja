"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/utils/cn";

type ButtonVariant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  fullWidth?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-400",
  secondary: "bg-slate-100 text-slate-900 hover:bg-slate-200 disabled:bg-slate-100",
  ghost: "bg-transparent text-slate-700 hover:bg-slate-100 disabled:text-slate-400"
};

export function Button({
  children,
  className,
  variant = "primary",
  fullWidth = false,
  ...props
}: ButtonProps): ReactNode {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed",
        variantClasses[variant],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
