"use client";

import Link from "next/link";
import { Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth.store";
import { useCartStore } from "@/store/cart.store";

function formatCurrency(value: string): string {
  return `R$ ${Number(value).toFixed(2).replace(".", ",")}`;
}

export default function CartPage() {
  const { user, isHydrated } = useAuthStore();
  const { cart, error, isLoading, isMutating, refreshCart, updateItemQuantity, removeItem } =
    useCartStore();
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!isHydrated || user?.role !== "customer") {
      return;
    }

    void refreshCart().catch(() => undefined);
  }, [isHydrated, refreshCart, user]);

  const cartSubtotal = useMemo(() => cart?.subtotal ?? "0.00", [cart]);
  const cartItems = cart?.items ?? [];

  if (isHydrated && user?.role !== "customer") {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <ShoppingBag className="mx-auto h-12 w-12 text-slate-300" />
          <h1 className="mt-4 text-2xl font-bold text-slate-900">Entre para acessar seu carrinho</h1>
          <p className="mt-2 text-sm text-slate-600">
            O carrinho da WM Distribuidora e vinculado ao cliente autenticado.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/cliente/login">
              <Button>Entrar</Button>
            </Link>
            <Link href="/">
              <Button variant="secondary">Continuar comprando</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  async function handleQuantityChange(itemId: string, quantity: number): Promise<void> {
    if (quantity < 1) {
      return;
    }
    try {
      setActionError(null);
      await updateItemQuantity(itemId, quantity);
    } catch (requestError) {
      setActionError(
        requestError instanceof Error
          ? requestError.message
          : "Nao foi possivel atualizar a quantidade do item."
      );
    }
  }

  async function handleRemoveItem(itemId: string): Promise<void> {
    try {
      setActionError(null);
      await removeItem(itemId);
    } catch (requestError) {
      setActionError(
        requestError instanceof Error
          ? requestError.message
          : "Nao foi possivel remover o item do carrinho."
      );
    }
  }

  const isEmpty = !isLoading && cartItems.length === 0;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Seu carrinho</h1>
          <p className="mt-2 text-sm text-slate-500">
            Revise os itens escolhidos antes de seguir para o fechamento.
          </p>
        </div>
        <Link href="/">
          <Button variant="secondary">Continuar comprando</Button>
        </Link>
      </div>

      {error ? <div className="mb-4"><Alert message={error} /></div> : null}
      {actionError ? <div className="mb-4"><Alert message={actionError} /></div> : null}

      {isLoading ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-sm text-slate-500">Carregando carrinho...</p>
        </div>
      ) : isEmpty ? (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm">
          <ShoppingBag className="mx-auto h-12 w-12 text-slate-300" />
          <h2 className="mt-4 text-xl font-semibold text-slate-900">Seu carrinho esta vazio</h2>
          <p className="mt-2 text-sm text-slate-600">
            Adicione produtos da vitrine para comecar a montar o pedido.
          </p>
          <div className="mt-6">
            <Link href="/">
              <Button>Ver produtos</Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[1.6fr_0.9fr]">
          <div className="space-y-4">
            {cartItems.map((item) => (
              <article
                key={item.id}
                className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap gap-2">
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                        {item.internal_code}
                      </span>
                      <span className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600">
                        {item.sku}
                      </span>
                    </div>
                    <h2 className="mt-3 text-lg font-semibold text-slate-900">{item.name}</h2>
                    <p className="mt-1 text-sm text-slate-600">
                      {item.product_name_base}
                      {item.brand ? ` • ${item.brand}` : ""}
                    </p>
                    <p className="mt-3 text-sm text-slate-500">
                      Estoque disponivel: {item.available_stock} unidade(s)
                    </p>
                  </div>

                  <div className="min-w-[180px] rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">Preco unitario</p>
                    <p className="mt-1 text-lg font-semibold text-slate-900">
                      {formatCurrency(item.unit_price)}
                    </p>
                    <p className="mt-3 text-xs uppercase tracking-wide text-slate-500">Total da linha</p>
                    <p className="mt-1 text-lg font-semibold text-blue-600">
                      {formatCurrency(item.line_total)}
                    </p>
                  </div>
                </div>

                <div className="mt-5 flex flex-col gap-4 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="inline-flex items-center rounded-full border border-slate-200 bg-white">
                    <button
                      type="button"
                      className="p-3 text-slate-600 hover:bg-slate-50 disabled:text-slate-300"
                      onClick={() => void handleQuantityChange(item.id, item.quantity - 1)}
                      disabled={item.quantity <= 1 || isMutating}
                    >
                      <Minus className="h-4 w-4" />
                    </button>
                    <span className="min-w-10 text-center text-sm font-semibold text-slate-900">
                      {item.quantity}
                    </span>
                    <button
                      type="button"
                      className="p-3 text-slate-600 hover:bg-slate-50 disabled:text-slate-300"
                      onClick={() => void handleQuantityChange(item.id, item.quantity + 1)}
                      disabled={item.quantity >= item.available_stock || isMutating}
                    >
                      <Plus className="h-4 w-4" />
                    </button>
                  </div>

                  <button
                    type="button"
                    className="inline-flex items-center gap-2 text-sm font-medium text-rose-600 hover:text-rose-700"
                    onClick={() => void handleRemoveItem(item.id)}
                    disabled={isMutating}
                  >
                    <Trash2 className="h-4 w-4" />
                    Remover item
                  </button>
                </div>
              </article>
            ))}
          </div>

          <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm h-fit">
            <h2 className="text-lg font-semibold text-slate-900">Resumo do pedido</h2>
            <div className="mt-6 space-y-3 text-sm text-slate-600">
              <div className="flex items-center justify-between">
                <span>Itens</span>
                <span>{cart?.total_items ?? 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Subtotal</span>
                <span className="font-medium text-slate-900">{formatCurrency(cartSubtotal)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Frete</span>
                <span>A calcular no checkout</span>
              </div>
            </div>

            <div className="mt-6 border-t border-slate-100 pt-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-700">Total parcial</span>
                <span className="text-2xl font-bold text-blue-600">{formatCurrency(cartSubtotal)}</span>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              <Link href="/checkout" className="block">
                <Button className="w-full">Ir para checkout</Button>
              </Link>
              <p className="text-xs leading-5 text-slate-500">
                O estoque ainda sera validado novamente no fechamento do pedido.
              </p>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
