import type { ApiResponse } from "@/types/api";

export type CartStatus = "active" | "converted" | "abandoned";

export interface CartSummary {
  total_items: number;
  subtotal: string;
}

export interface CartItem {
  id: string;
  product_item_id: string;
  internal_code: string;
  sku: string;
  name: string;
  product_name_base: string;
  brand: string | null;
  quantity: number;
  unit_price: string;
  line_total: string;
  available_stock: number;
  created_at: string;
  updated_at: string;
}

export interface CartResponse {
  id: string;
  status: CartStatus;
  items: CartItem[];
  subtotal: string;
  total_items: number;
  summary: CartSummary;
  created_at: string;
  updated_at: string;
}

export interface CartItemCreatePayload {
  product_item_id: string;
  quantity: number;
}

export interface CartItemUpdatePayload {
  quantity: number;
}

export type CartApiResponse = ApiResponse<CartResponse>;
