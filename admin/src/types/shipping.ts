import type { ApiResponse } from "@/types/api";

export interface ShippingStoreConfigPayload {
  store_name: string;
  zip_code: string;
  street: string;
  number: string;
  district: string;
  city: string;
  state: string;
  complement?: string | null;
}

export interface ShippingStoreConfig {
  id: string;
  store_name: string;
  zip_code: string;
  street: string;
  number: string;
  district: string;
  city: string;
  state: string;
  complement: string | null;
  latitude: string | null;
  longitude: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ShippingDistanceRulePayload {
  rule_name: string;
  max_distance_km: string;
  shipping_price: string;
  estimated_time_text?: string | null;
  sort_order: number;
}

export interface ShippingDistanceRule extends ShippingDistanceRulePayload {
  id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type ShippingStoreConfigResponse = ApiResponse<ShippingStoreConfig | null>;
export type ShippingStoreConfigSaveResponse = ApiResponse<ShippingStoreConfig>;
export type ShippingDistanceRuleListResponse = ApiResponse<ShippingDistanceRule[]>;
export type ShippingDistanceRuleResponse = ApiResponse<ShippingDistanceRule>;
