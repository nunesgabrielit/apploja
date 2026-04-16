"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle, ChevronLeft, Package, ShoppingCart, Tag } from "lucide-react";
import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { getProduct, getProductItem } from "@/services/catalog.service";
import { useAuthStore } from "@/store/auth.store";
import { useCartStore } from "@/store/cart.store";
import type { ProductItemRead, ProductItemSummary, ProductRead } from "@/types/catalog";

function formatCurrency(value: string): string {
  return `R$ ${Number(value).toFixed(2).replace(".", ",")}`;
}

export default function ProductDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;
  const user = useAuthStore((state) => state.user);
  const addItem = useCartStore((state) => state.addItem);
  const isCartMutating = useCartStore((state) => state.isMutating);

  const [product, setProduct] = useState<ProductRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<ProductItemSummary | null>(null);
  const [selectedItemDetails, setSelectedItemDetails] = useState<ProductItemRead | null>(null);
  const [cartMessage, setCartMessage] = useState<string | null>(null);
  const [cartError, setCartError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProduct() {
      try {
        const response = await getProduct(productId);
        setProduct(response.data);
        if (response.data.items.length > 0) {
          setSelectedItem(response.data.items[0]);
        }
      } catch {
        setError("Produto nao encontrado ou indisponivel.");
      } finally {
        setLoading(false);
      }
    }

    if (productId) {
      void loadProduct();
    }
  }, [productId]);

  useEffect(() => {
    async function loadSelectedItem() {
      if (!selectedItem) {
        setSelectedItemDetails(null);
        return;
      }

      try {
        const response = await getProductItem(selectedItem.id);
        setSelectedItemDetails(response.data);
      } catch {
        setSelectedItemDetails(null);
      }
    }

    void loadSelectedItem();
  }, [selectedItem]);

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="animate-pulse space-y-8">
          <div className="h-4 w-32 rounded bg-slate-200" />
          <div className="flex flex-col gap-8 md:flex-row">
            <div className="aspect-square w-full rounded-2xl bg-slate-200 md:w-1/2" />
            <div className="w-full space-y-4 md:w-1/2">
              <div className="h-8 w-3/4 rounded bg-slate-200" />
              <div className="h-4 w-1/4 rounded bg-slate-200" />
              <div className="h-32 w-full rounded bg-slate-200" />
              <div className="h-10 w-1/3 rounded bg-slate-200" />
              <div className="h-12 w-full rounded bg-slate-200" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="mx-auto flex max-w-7xl flex-col items-center px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-6 w-full max-w-md text-center">
          <Alert message={error || "Erro ao carregar produto."} />
        </div>
        <Button onClick={() => router.push("/")}>
          <ChevronLeft className="mr-2 h-4 w-4" />
          Voltar para a vitrine
        </Button>
      </div>
    );
  }

  async function handleAddToCart(): Promise<void> {
    if (!selectedItem) {
      return;
    }

    if (user?.role !== "customer") {
      router.push("/cliente/login");
      return;
    }

    try {
      setCartError(null);
      await addItem(selectedItem.id, 1);
      setCartMessage(`${selectedItem.name} foi adicionado ao carrinho.`);
    } catch (requestError) {
      setCartMessage(null);
      setCartError(requestError instanceof Error ? requestError.message : "Nao foi possivel adicionar ao carrinho.");
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <nav className="mb-8 flex text-sm font-medium text-slate-500">
        <Link href="/" className="hover:text-blue-600 transition-colors">
          Home
        </Link>
        <span className="mx-2">/</span>
        <span>{product.category.name}</span>
        <span className="mx-2">/</span>
        <span className="text-slate-900">{product.name_base}</span>
      </nav>

      <div className="flex flex-col gap-12 md:flex-row">
        <div className="w-full md:w-1/2">
          <div className="relative aspect-square w-full overflow-hidden rounded-3xl border border-slate-200 bg-slate-50 shadow-sm">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name_base}
                className="h-full w-full object-cover object-center"
              />
            ) : (
              <div className="flex h-full w-full flex-col items-start justify-between bg-[radial-gradient(circle_at_top_left,_rgba(37,99,235,0.14),_transparent_35%),linear-gradient(135deg,#0f172a_0%,#1e293b_55%,#334155_100%)] p-8 text-white">
                <div className="rounded-full border border-white/20 bg-white/10 p-3">
                  <Package className="h-8 w-8" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.32em] text-slate-200">
                    {product.category.name}
                  </p>
                  <h1 className="mt-3 text-3xl font-semibold leading-tight">{product.name_base}</h1>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex w-full flex-col md:w-1/2">
          <div className="flex flex-wrap items-center gap-3">
            {product.brand ? (
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-700">
                {product.brand}
              </span>
            ) : null}
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
              {product.category.name}
            </span>
          </div>

          <h1 className="mt-4 text-3xl font-bold text-slate-900">{product.name_base}</h1>
          <p className="mt-4 text-base leading-7 text-slate-600">
            {product.description || "Produto sem descricao comercial cadastrada."}
          </p>

          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">
              Variacoes disponiveis
            </h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {product.items.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setSelectedItem(item)}
                  className={`rounded-xl border px-4 py-3 text-left text-sm transition-colors ${
                    selectedItem?.id === item.id
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <p className="font-medium">{item.internal_code}</p>
                  <p className="mt-1 max-w-[220px] text-xs leading-5">{item.name}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            {selectedItem ? (
              <>
                <div className="flex flex-col gap-4 border-b border-slate-100 pb-5 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                        <Tag className="mr-1.5 h-3.5 w-3.5" />
                        Codigo {selectedItem.internal_code}
                      </span>
                      <span className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600">
                        {selectedItem.sku}
                      </span>
                    </div>
                    <h2 className="mt-3 text-xl font-semibold text-slate-900">{selectedItem.name}</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      {selectedItemDetails?.short_description || "Item vendavel importado do catalogo WM Distribuidora."}
                    </p>
                  </div>
                  <div className="text-left sm:text-right">
                    <p className="text-xs uppercase tracking-wide text-slate-500">Preco</p>
                    <p className="mt-1 text-3xl font-bold text-blue-600">
                      {formatCurrency(selectedItem.price)}
                    </p>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">Estoque atual</p>
                    <p
                      className={`mt-2 text-lg font-semibold ${
                        selectedItem.stock_current > 0 ? "text-emerald-600" : "text-rose-600"
                      }`}
                    >
                      {selectedItem.stock_current} unidade(s)
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">Estoque minimo</p>
                    <p className="mt-2 text-lg font-semibold text-slate-900">
                      {selectedItem.stock_minimum} unidade(s)
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">Conector</p>
                    <p className="mt-2 text-base font-medium text-slate-900">
                      {selectedItemDetails?.connector_type || "Nao informado"}
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">Potencia / Voltagem</p>
                    <p className="mt-2 text-base font-medium text-slate-900">
                      {[selectedItemDetails?.power, selectedItemDetails?.voltage].filter(Boolean).join(" • ") ||
                        "Nao informado"}
                    </p>
                  </div>
                </div>

                <div className="mt-6">
                  <Button
                    className="h-12 w-full text-lg"
                    disabled={selectedItem.stock_current <= 0 || isCartMutating}
                    onClick={() => void handleAddToCart()}
                  >
                    <ShoppingCart className="mr-2 h-5 w-5" />
                    {selectedItem.stock_current > 0
                      ? isCartMutating
                        ? "Adicionando..."
                        : "Adicionar ao carrinho"
                      : "Esgotado"}
                  </Button>

                  {cartMessage ? (
                    <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                      {cartMessage}{" "}
                      <button
                        type="button"
                        className="font-semibold underline"
                        onClick={() => router.push("/carrinho")}
                      >
                        Ver carrinho
                      </button>
                    </div>
                  ) : null}

                  {cartError ? <div className="mt-3"><Alert message={cartError} /></div> : null}

                  <div className="mt-4 flex items-center justify-center space-x-2 text-sm text-slate-500">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Item real vendido por codigo, SKU e variacao tecnica</span>
                  </div>
                </div>
              </>
            ) : (
              <Button className="h-12 w-full" disabled>
                Selecione uma opcao
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
