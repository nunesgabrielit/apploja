"use client";

import { useEffect, useState } from "react";
import { Package } from "lucide-react";

import { ProductCard, ProductCardSkeleton } from "@/components/shop/product-card";
import { Alert } from "@/components/ui/alert";
import { listProducts } from "@/services/catalog.service";
import type { ProductListItem } from "@/types/catalog";

export default function StorefrontHome() {
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProducts() {
      try {
        const response = await listProducts({ page: 1, page_size: 12 });
        setProducts(response.data);
      } catch {
        setError("Falha ao carregar o catalogo de produtos. Tente novamente mais tarde.");
      } finally {
        setLoading(false);
      }
    }

    void loadProducts();
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.18),_transparent_28%),linear-gradient(135deg,#ffffff_0%,#f8fafc_45%,#e2e8f0_100%)] px-6 py-10 shadow-sm sm:px-8 lg:px-10">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.28em] text-blue-700">
            WM Distribuidora
          </p>
          <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Catalogo profissional com itens reais, codigos e especificacoes do seu estoque.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
            Explore produtos organizados por linha comercial, com variacoes vendaveis,
            codigos internos e precos prontos para o fluxo de compra.
          </p>
        </div>
      </section>

      <div className="mb-8 mt-10 flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Produtos em destaque</h2>
          <p className="mt-2 text-sm text-slate-500">
            Selecao inicial do catalogo importado diretamente do PDF comercial.
          </p>
        </div>
        {!loading && products.length > 0 ? (
          <div className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm">
            {products.length} produto(s) exibidos nesta vitrine
          </div>
        ) : null}
      </div>

      {error ? (
        <div className="mb-6">
          <Alert message={error} />
        </div>
      ) : null}

      {loading ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <ProductCardSkeleton key={index} />
          ))}
        </div>
      ) : products.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white py-16 shadow-sm">
          <Package className="mb-4 h-12 w-12 text-slate-400" />
          <h3 className="text-lg font-medium text-slate-900">Nenhum produto encontrado</h3>
          <p className="mt-1 text-sm text-slate-500">
            Ainda nao ha produtos ativos cadastrados no sistema.
          </p>
        </div>
      )}
    </div>
  );
}
