export type LoginRole = "admin" | "employee" | "customer";

interface LoginOption {
  role: LoginRole;
  label: string;
  hint: string;
}

export const LOGIN_OPTIONS: LoginOption[] = [
  {
    role: "customer",
    label: "Area do Cliente",
    hint: "Acompanhe pedidos, carrinho e perfil."
  },
  {
    role: "employee",
    label: "Area de Funcionarios",
    hint: "Acesse o painel operacional da equipe."
  },
  {
    role: "admin",
    label: "Area do Administrador",
    hint: "Gerencie o painel e a operacao."
  }
];

export function normalizeLoginRole(
  value: string | null | undefined,
  fallback: LoginRole = "customer"
): LoginRole {
  if (value === "admin" || value === "employee" || value === "customer") {
    return value;
  }

  return fallback;
}

export function getLoginHref(role: LoginRole): string {
  if (role === "customer") {
    return "/cliente/login";
  }

  return `/admin/login?role=${role}`;
}

export function getPostLoginHref(role: LoginRole): string {
  if (role === "customer") {
    return "/perfil";
  }

  return "/admin/dashboard";
}

export function getLoginPageCopy(role: LoginRole): {
  eyebrow: string;
  title: string;
  description: string;
  submitLabel: string;
} {
  switch (role) {
    case "admin":
      return {
        eyebrow: "Acesso administrativo",
        title: "Conectar como admin",
        description: "Entre com seu e-mail para acessar a gestao completa da plataforma.",
        submitLabel: "Entrar como admin"
      };
    case "employee":
      return {
        eyebrow: "Acesso da equipe",
        title: "Conectar como funcionario",
        description: "Entre com seu e-mail para acessar o painel operacional.",
        submitLabel: "Entrar como funcionario"
      };
    default:
      return {
        eyebrow: "Acesso do cliente",
        title: "Conectar com e-mail",
        description: "Entre para acompanhar pedidos, carrinho e dados da sua conta.",
        submitLabel: "Entrar como cliente"
      };
  }
}
