import type { ApiResponse } from "@/types/api";
import type { FulfillmentType } from "@/types/order";

export interface ShippingCalculatePayload {
  zip_code?: string | null;
  address_id?: string | null;
  fulfillment_type: FulfillmentType;
}

export interface ShippingCalculateResponse {
  zip_code: string | null;
  zip_code_normalized: string | null;
  fulfillment_type: FulfillmentType;
  shipping_price: string;
  estimated_time_text: string | null;
  rule_name: string;
  covered: boolean;
  calculation_mode: "pickup" | "distance" | "zip_code";
  distance_km: string | null;
}

export type ShippingCalculateApiResponse = ApiResponse<ShippingCalculateResponse>;
