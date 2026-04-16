import Link from "next/link";
import { Package } from "lucide-react";
import type { ProductListItem } from "@/types/catalog";

interface ProductCardProps {
  product: ProductListItem;
}

export function ProductCard({ product }: ProductCardProps) {
  // Pega o menor preço dentre as variações ativas (product items)
  const availableItems = product.items || [];
  const lowestPrice = availableItems.length > 0 
    ? Math.min(...availableItems.map((item) => Number(item.price)))
    : null;

  return (
    <Link href={`/produto/${product.id}`} className="group relative flex flex-col overflow-hidden rounded-lg border border-slate-200 bg-white p-4 transition-all hover:shadow-md">
      <div className="aspect-[4/3] w-full overflow-hidden rounded-md bg-slate-100 mb-4 flex items-center justify-center">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name_base}
            className="h-full w-full object-cover object-center transition-transform group-hover:scale-105"
          />
        ) : (
          <Package className="h-12 w-12 text-slate-300" />
        )}
      </div>
      
      <div className="flex flex-1 flex-col">
        {product.brand && (
          <p className="text-xs font-medium text-slate-500 mb-1">{product.brand}</p>
        )}
        <h3 className="text-sm font-medium text-slate-900 mb-2 flex-1 line-clamp-2">
          {product.name_base}
        </h3>
        
        <div className="mt-auto pt-2 border-t border-slate-100 flex items-center justify-between">
          {lowestPrice !== null ? (
            <div>
              <span className="text-xs text-slate-500">a partir de</span>
              <p className="text-lg font-bold text-blue-600">
                R$ {lowestPrice.toFixed(2).replace(".", ",")}
              </p>
            </div>
          ) : (
            <p className="text-sm font-medium text-slate-400">Indisponível</p>
          )}
        </div>
      </div>
    </Link>
  );
}

export function ProductCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-slate-200 bg-white p-4 animate-pulse">
      <div className="aspect-[4/3] w-full rounded-md bg-slate-200 mb-4"></div>
      <div className="h-3 w-1/3 bg-slate-200 rounded mb-2"></div>
      <div className="h-4 w-full bg-slate-200 rounded mb-1"></div>
      <div className="h-4 w-2/3 bg-slate-200 rounded mb-4"></div>
      <div className="mt-auto pt-2 border-t border-slate-100">
        <div className="h-3 w-1/4 bg-slate-200 rounded mb-1"></div>
        <div className="h-6 w-1/2 bg-slate-200 rounded"></div>
      </div>
    </div>
  );
}
