import { api } from "@/services/api";
import type {
  ShippingDistanceRuleListResponse,
  ShippingDistanceRulePayload,
  ShippingDistanceRuleResponse,
  ShippingStoreConfigPayload,
  ShippingStoreConfigResponse,
  ShippingStoreConfigSaveResponse
} from "@/types/shipping";

export async function getStoreShippingConfig(): Promise<ShippingStoreConfigResponse> {
  const { data } = await api.get<ShippingStoreConfigResponse>("/admin/shipping-rules/store-config");
  return data;
}

export async function saveStoreShippingConfig(
  payload: ShippingStoreConfigPayload
): Promise<ShippingStoreConfigSaveResponse> {
  const { data } = await api.put<ShippingStoreConfigSaveResponse>(
    "/admin/shipping-rules/store-config",
    payload
  );
  return data;
}

export async function listDistanceShippingRules(): Promise<ShippingDistanceRuleListResponse> {
  const { data } = await api.get<ShippingDistanceRuleListResponse>("/admin/shipping-rules/distance");
  return data;
}

export async function createDistanceShippingRule(
  payload: ShippingDistanceRulePayload
): Promise<ShippingDistanceRuleResponse> {
  const { data } = await api.post<ShippingDistanceRuleResponse>("/admin/shipping-rules/distance", payload);
  return data;
}

export async function updateDistanceShippingRule(
  ruleId: string,
  payload: Partial<ShippingDistanceRulePayload> & { is_active?: boolean }
): Promise<ShippingDistanceRuleResponse> {
  const { data } = await api.put<ShippingDistanceRuleResponse>(
    `/admin/shipping-rules/distance/${ruleId}`,
    payload
  );
  return data;
}

export async function deleteDistanceShippingRule(ruleId: string): Promise<ShippingDistanceRuleResponse> {
  const { data } = await api.delete<ShippingDistanceRuleResponse>(
    `/admin/shipping-rules/distance/${ruleId}`
  );
  return data;
}
