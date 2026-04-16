import type { PaginatedResponse } from "@/types/api";

export interface CategorySummary {
  id: string;
  name: string;
}

export interface CategoryListItem {
  id: string;
  name: string;
  description: string | null;
}

export interface ProductItemSummary {
  id: string;
  internal_code: string;
  sku: string;
  name: string;
  price: string;
  stock_current: number;
  stock_minimum: number;
  low_stock: boolean;
}

export interface ProductListItem {
  id: string;
  category: CategorySummary;
  name_base: string;
  brand: string | null;
  description: string | null;
  image_url: string | null;
  items: ProductItemSummary[];
}

export interface ProductRead extends ProductListItem {
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductItemListItem {
  id: string;
  product_id: string;
  category_id: string;
  brand: string | null;
  internal_code: string;
  sku: string;
  name: string;
  product_name_base: string;
  price: string;
  stock_current: number;
  stock_minimum: number;
  low_stock: boolean;
}

export interface ProductCreatePayload {
  category_id: string;
  name_base: string;
  brand?: string | null;
  description?: string | null;
  image_url?: string | null;
}

export interface ProductUpdatePayload {
  category_id?: string;
  name_base?: string;
  brand?: string | null;
  description?: string | null;
  image_url?: string | null;
  is_active?: boolean;
}

export type StockOperation = "set" | "increment" | "decrement";

export interface ProductItemStockUpdatePayload {
  quantity: number;
  operation: StockOperation;
  reason?: string | null;
}

export interface StockMovementItem {
  id: string;
  product_item_id: string;
  movement_type: "sale" | "manual_adjustment" | "cancellation" | "return";
  quantity: number;
  source: "order" | "admin" | "system";
  reference_id: string | null;
  performed_by_user_id: string | null;
  created_at: string;
}

export type CategoryListResponse = PaginatedResponse<CategoryListItem>;
export type ProductListResponse = PaginatedResponse<ProductListItem>;
export type ProductItemListResponse = PaginatedResponse<ProductItemListItem>;
export type StockMovementListResponse = PaginatedResponse<StockMovementItem>;
