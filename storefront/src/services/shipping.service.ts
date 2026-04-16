import { api } from "@/services/api";
import type { ShippingCalculateApiResponse, ShippingCalculatePayload } from "@/types/shipping";

export async function calculateShipping(
  payload: ShippingCalculatePayload
): Promise<ShippingCalculateApiResponse> {
  const { data } = await api.post<ShippingCalculateApiResponse>("/shipping/calculate", payload);
  return data;
}
