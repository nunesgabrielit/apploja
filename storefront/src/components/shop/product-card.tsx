import Link from "next/link";
import { Package } from "lucide-react";

import type { ProductListItem } from "@/types/catalog";

interface ProductCardProps {
  product: ProductListItem;
}

function formatCurrency(value: number): string {
  return `R$ ${value.toFixed(2).replace(".", ",")}`;
}

function buildCodePreview(product: ProductListItem): string[] {
  return product.items.slice(0, 3).map((item) => item.internal_code);
}

export function ProductCard({ product }: ProductCardProps) {
  const availableItems = product.items || [];
  const lowestPrice =
    availableItems.length > 0 ? Math.min(...availableItems.map((item) => Number(item.price))) : null;
  const codePreview = buildCodePreview(product);

  return (
    <Link
      href={`/produto/${product.id}`}
      className="group relative flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg"
    >
      <div className="relative aspect-[4/3] w-full overflow-hidden border-b border-slate-100 bg-gradient-to-br from-slate-50 via-white to-slate-100">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name_base}
            className="h-full w-full object-cover object-center transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-start justify-between bg-[radial-gradient(circle_at_top_left,_rgba(37,99,235,0.12),_transparent_38%),linear-gradient(135deg,#0f172a_0%,#1e293b_55%,#334155_100%)] p-5 text-white">
            <div className="rounded-full border border-white/20 bg-white/10 p-2">
              <Package className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-slate-200">
                {product.category.name}
              </p>
              <p className="mt-2 text-lg font-semibold leading-tight">{product.name_base}</p>
            </div>
          </div>
        )}
        <div className="absolute left-4 top-4 flex flex-wrap gap-2">
          <span className="rounded-full bg-white/90 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-700 shadow-sm">
            {product.category.name}
          </span>
          {product.brand ? (
            <span className="rounded-full bg-slate-900/85 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-white shadow-sm">
              {product.brand}
            </span>
          ) : null}
        </div>
      </div>

      <div className="flex flex-1 flex-col p-5">
        <h3 className="text-base font-semibold text-slate-900 line-clamp-2">{product.name_base}</h3>
        <p className="mt-2 min-h-[40px] text-sm leading-5 text-slate-600 line-clamp-2">
          {product.description || "Produto importado do catalogo tecnico da WM Distribuidora."}
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          {codePreview.map((code) => (
            <span
              key={code}
              className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600"
            >
              {code}
            </span>
          ))}
          {availableItems.length > 3 ? (
            <span className="rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-[11px] font-medium text-blue-700">
              +{availableItems.length - 3} variacoes
            </span>
          ) : null}
        </div>

        <div className="mt-5 flex items-end justify-between border-t border-slate-100 pt-4">
          {lowestPrice !== null ? (
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Preco inicial</p>
              <p className="mt-1 text-2xl font-bold text-blue-600">{formatCurrency(lowestPrice)}</p>
            </div>
          ) : (
            <p className="text-sm font-medium text-slate-400">Sem variacoes ativas</p>
          )}
          <div className="text-right text-xs text-slate-500">
            <p>{availableItems.length} item(ns)</p>
            <p className="mt-1 font-medium text-slate-700">Ver detalhes</p>
          </div>
        </div>
      </div>
    </Link>
  );
}

export function ProductCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm animate-pulse">
      <div className="aspect-[4/3] w-full rounded-xl bg-slate-200 mb-4" />
      <div className="h-4 w-1/3 rounded bg-slate-200" />
      <div className="mt-3 h-5 w-4/5 rounded bg-slate-200" />
      <div className="mt-2 h-4 w-full rounded bg-slate-200" />
      <div className="mt-2 h-4 w-3/4 rounded bg-slate-200" />
      <div className="mt-4 flex gap-2">
        <div className="h-6 w-16 rounded-full bg-slate-200" />
        <div className="h-6 w-16 rounded-full bg-slate-200" />
      </div>
      <div className="mt-5 border-t border-slate-100 pt-4">
        <div className="h-3 w-24 rounded bg-slate-200" />
        <div className="mt-2 h-7 w-28 rounded bg-slate-200" />
      </div>
    </div>
  );
}
